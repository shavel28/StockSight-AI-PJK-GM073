import os
import uuid
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from prophet import Prophet
import traceback
import json
from prophet.serialize import model_from_json
import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

app = FastAPI(title="Stocksight AI Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users_db = {}
products_db = {}
inventory_db = {}
uploads_status = {}
forecasts_status = {}
forecasts_results = {}
raw_data_db = pd.DataFrame() 

ai_config_db = {
    "default_horizon": 30,
    "forecast_scenario": "expected", 
    "growth_factor": 0.0 
}

@app.on_event("startup")
async def load_initial_data():
    global raw_data_db, products_db, inventory_db
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    processed_dir = os.path.join(base_dir, "processed_data")
    
    sales_path = os.path.join(processed_dir, "time_series_category_feature_engineered.csv")
    inv_path = os.path.join(processed_dir, "inventory_summary.csv")

    if os.path.exists(sales_path):
        try:
            df_sales = pd.read_csv(sales_path)
            if "ds" in df_sales.columns:
                df_sales["ds"] = pd.to_datetime(df_sales["ds"])
            if "y" in df_sales.columns:
                df_sales["y"] = pd.to_numeric(df_sales["y"], errors="coerce").fillna(0)
            
            raw_data_db = df_sales.copy()
            
            if "Category" in df_sales.columns:
                unique_products = df_sales[["Category"]].drop_duplicates()
                for _, row in unique_products.iterrows():
                    pid = str(uuid.uuid4())[:8]
                    products_db[pid] = {
                        "name": row["Category"],
                        "category": row["Category"]
                    }
            print(f"[INFO] Berhasil memuat {len(products_db)} produk dari data sales.")
        except Exception as e:
            print(f"[ERROR] Gagal memuat csv: {e}")

    if os.path.exists(inv_path):
        try:
            df_inv = pd.read_csv(inv_path)
            if "Category" in df_inv.columns:
                for _, row in df_inv.iterrows():
                    cat_name = row["Category"]
                    existing_pid = next((k for k, v in products_db.items() if v["category"] == cat_name), None)
                    
                    if not existing_pid:
                        pid = str(uuid.uuid4())[:8]
                        products_db[pid] = {
                            "name": cat_name,
                            "category": cat_name
                        }
                    else:
                        pid = existing_pid
                        
                    safety_stock = int(row.get("Safety Stock", 0))
                    rop = int(row.get("Reorder Point (ROP)", 0))
                    initial_stock = rop + 1500 if rop > 0 else 0
                    
                    inventory_db[pid] = {
                        "current_stock": initial_stock, 
                        "safety_stock": safety_stock,
                        "reorder_point": rop
                    }
            print(f"[INFO] Berhasil memuat data inventory dari {inv_path}")
        except Exception as e:
            print(f"[ERROR] Gagal memuat inventory_summary.csv: {e}")
    else:
        for pid in products_db.keys():
            inventory_db[pid] = {"current_stock": 50, "safety_stock": 15, "reorder_point": 25}
            
@app.get("/api/v1/debug")
def debug():
    return {
        "products": products_db,
        "inventory": inventory_db,
        "columns": raw_data_db.columns.tolist(),
        "rows": len(raw_data_db)
    }

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class StockUpdate(BaseModel):
    current_stock: int

class ForecastRequest(BaseModel):
    product_id: str
    model: str
    horizon_days: Optional[int] = None
    include_holidays: bool

class AIConfig(BaseModel):
    default_horizon: int = 30
    forecast_scenario: str = "expected"
    growth_factor: float = 0.0
    changepoint_prior_scale: Optional[float] = 0.05
    seasonality_prior_scale: Optional[float] = 10.0
    seasonality_mode: Optional[str] = "additive"

@app.post("/api/v1/auth/register")
def register(user: UserRegister):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    users_db[user.email] = {"name": user.name, "password": user.password}
    return {"message": "Registrasi berhasil"}

@app.post("/api/v1/auth/login")
def login(user: UserLogin):
    if user.email not in users_db or users_db[user.email]["password"] != user.password:
        raise HTTPException(status_code=401, detail="Kredensial tidak valid")
    return {"access_token": f"fake-jwt-token-{user.email}", "token_type": "bearer"}

@app.get("/api/v1/auth/session")
def check_session(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesi tidak valid.")
    
    token = authorization.split(" ")[1]
    
    
    if token.startswith("fake-jwt-token-"):
        email = token.replace("fake-jwt-token-", "")
        
        if email in users_db:
            return {"message": "Sesi aktif", "user": users_db[email]["name"]}
            
    
    raise HTTPException(status_code=401, detail="Sesi telah berakhir.")


@app.get("/api/v1/config")
def get_config():
    return ai_config_db

@app.post("/api/v1/config")
def update_config(config: AIConfig):
    global ai_config_db
    ai_config_db.update(config.dict())
    return {"message": "Skenario bisnis berhasil disimpan"}

@app.get("/api/v1/dashboard/summary")
def get_summary():
    total_sales = 0
    if not raw_data_db.empty:
        if "y" in raw_data_db.columns:
            total_sales = int(pd.to_numeric(raw_data_db["y"], errors="coerce").fillna(0).sum())

    ai_accuracy = None 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    metrics_path = os.path.join(base_dir, "processed_data", "model_metrics.csv")
    
    if os.path.exists(metrics_path):
        try:
            df_metrics = pd.read_csv(metrics_path)
            if "accuracy" in df_metrics.columns:
                ai_accuracy = round(df_metrics["accuracy"].mean(), 1)
        except Exception as e:
            print(f"[WARNING] Gagal membaca metrics CSV: {e}")

    return {
        "total_sales": total_sales,
        "total_products": len(products_db),
        "ai_accuracy": ai_accuracy  
    }

@app.get("/api/v1/dashboard/top-products")
def get_top_products():
    if raw_data_db.empty:
        return []

    top = (
        raw_data_db
        .groupby("Category")["y"]
        .sum()
        .reset_index()
        .sort_values("y", ascending=False)
        .head(5)
    )

    return [{"product_name": row["Category"], "total_sold": int(row["y"])} for _, row in top.iterrows()]

@app.get("/api/v1/inventory/reorder")
def get_inventory():
    result = []
    for pid, p in products_db.items():
        inv = inventory_db.get(pid, {"current_stock": 0, "safety_stock": 10, "reorder_point": 20})
        needs_reorder = inv["current_stock"] <= inv["reorder_point"]
        result.append({
            "product_id": pid,
            "product_name": p["name"],
            "current_stock": inv["current_stock"],
            "safety_stock": inv["safety_stock"],
            "reorder_point": inv["reorder_point"],
            "needs_reorder": needs_reorder
        })
    return result

@app.patch("/api/v1/products/{product_id}/stock")
def update_stock(product_id: str, stock_data: StockUpdate):
    if product_id not in inventory_db:
        inventory_db[product_id] = {"current_stock": 0, "safety_stock": 10, "reorder_point": 20}
    inventory_db[product_id]["current_stock"] = stock_data.current_stock
    return {"message": "Stok berhasil diperbarui"}

@app.get("/api/v1/products")
def get_products():
    return [{"id": pid, "product_name": p["name"], "category": p.get("category", "General")} for pid, p in products_db.items()]

async def process_csv_pipeline(upload_id: str, df: pd.DataFrame):
    global raw_data_db, products_db, inventory_db
    try:
        await asyncio.sleep(2) 
        required_cols = ["Category", "ds", "y"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Kolom wajib hilang: {col}")
                
        df["ds"] = pd.to_datetime(df["ds"])
        df["y"] = pd.to_numeric(df["y"], errors="coerce").fillna(0)
        
        raw_data_db = pd.concat([raw_data_db, df]).drop_duplicates()
        
        unique_products = df.drop_duplicates(subset=["Category"])
        for _, row in unique_products.iterrows():
            name = row["Category"]
            existing_id = next((k for k, v in products_db.items() if v["name"] == name), None)
            
            if not existing_id:
                pid = str(uuid.uuid4())[:8]
                products_db[pid] = {"name": name, "category": name}
                inventory_db[pid] = {"current_stock": 0, "safety_stock": 0, "reorder_point": 0}
                
        uploads_status[upload_id] = "done"
    except Exception as e:
        uploads_status[upload_id] = "error"
        print(f"Pipeline Error: {e}")

@app.post("/api/v1/uploads")
async def upload_data(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Hanya menerima format CSV")
    upload_id = str(uuid.uuid4())
    uploads_status[upload_id] = "processing"
    df = pd.read_csv(file.file)
    asyncio.create_task(process_csv_pipeline(upload_id, df))
    return {"id": upload_id, "message": "File sedang diproses"}

@app.get("/api/v1/uploads/{upload_id}")
def check_upload_status(upload_id: str):
    return {"status": uploads_status.get(upload_id, "error")}

async def run_prophet_model(forecast_id: str, product_id: str, horizon: int):
    try:
        await asyncio.sleep(1)

        product_name = products_db[product_id]["name"]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # PERBAIKAN: Hapus ".."
        model_filename = f"prophet_model_{product_name.replace(' ', '_')}.json"
        model_path = os.path.join(base_dir, "Notebooks", model_filename)
        
        if not os.path.exists(model_path):
            print(f"\n[AWAS] File {model_filename} tidak ditemukan!")
            # PERBAIKAN: Hapus ".."
            fallback_path = os.path.join(base_dir, "Notebooks", "prophet_model.json")
            if os.path.exists(fallback_path):
                model_path = fallback_path
            else:
                raise FileNotFoundError(f"File model {model_filename} tidak ditemukan!")

        with open(model_path, 'r') as fin:
            m = model_from_json(fin.read())

        future = m.make_future_dataframe(periods=horizon)
        
        if hasattr(m, 'extra_regressors'):
            for reg_name in m.extra_regressors.keys():
                future[reg_name] = 0
                
        forecast = m.predict(future)

        df_product = raw_data_db[raw_data_db["Category"] == product_name].copy()
        
        if len(df_product) < 5:
            print(f"[ERROR] Data historis untuk {product_name} kosong atau kurang dari 5 baris!")
            forecasts_status[forecast_id] = "error"
            return
            
        df_prophet = df_product.groupby("ds", as_index=False)["y"].sum().sort_values("ds")
        df_prophet["ds"] = pd.to_datetime(df_prophet["ds"]).dt.tz_localize(None)
        df_prophet["y"] = pd.to_numeric(df_prophet["y"], errors="coerce").fillna(0)

        historical_forecast = forecast.set_index('ds')[['yhat']].join(df_prophet.set_index('ds')[['y']]).dropna()
        historical_forecast.reset_index(inplace=True)
        
        historical_forecast['month_year'] = historical_forecast['ds'].dt.to_period('M')
        monthly_df = historical_forecast.groupby('month_year')[['y', 'yhat']].sum().reset_index()
        monthly_df = monthly_df[monthly_df['y'] > 0]
        
        if not monthly_df.empty:
            y_true_m = monthly_df['y']
            y_pred_m = monthly_df['yhat']
            
            real_mape = mean_absolute_percentage_error(y_true_m, y_pred_m) * 100
            real_rmse = np.sqrt(mean_squared_error(y_true_m, y_pred_m))
        else:
            real_mape = 0
            real_rmse = 0

        history = []
        for _, row in df_prophet.tail(min(horizon, len(df_prophet))).iterrows():
            history.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "qty": round(row["y"], 2)
            })

        forecast_data = []
        future_forecast = forecast.tail(horizon)
        
        scenario = ai_config_db.get("forecast_scenario", "expected")
        growth = ai_config_db.get("growth_factor", 0.0) / 100.0

        for _, row in future_forecast.iterrows():
            if scenario == "optimistic":
                base_qty = row["yhat_upper"]
            elif scenario == "pessimistic":
                base_qty = row["yhat_lower"]
            else:
                base_qty = row["yhat"]
            
            final_qty = base_qty * (1 + growth)

            forecast_data.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "qty": max(0, round(final_qty, 2))
            })

        forecasts_results[forecast_id] = {
            "mape": round(real_mape, 2), 
            "rmse": round(real_rmse, 2),
            "history": history,
            "forecast": forecast_data
        }

        forecasts_status[forecast_id] = "done"

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("MODEL ERROR:", repr(e))
        forecasts_status[forecast_id] = "error"

@app.post("/api/v1/forecasts")
async def trigger_forecast(req: ForecastRequest): 
    if req.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        
    forecast_id = str(uuid.uuid4())
    forecasts_status[forecast_id] = "processing"
    
    horizon = req.horizon_days if req.horizon_days else ai_config_db["default_horizon"]
    
    asyncio.create_task(run_prophet_model(forecast_id, req.product_id, horizon))
    return {"id": forecast_id, "message": "Model Prophet sedang dijalankan"}

@app.get("/api/v1/forecasts/{forecast_id}")
def check_forecast_status(forecast_id: str):
    return {"status": forecasts_status.get(forecast_id, "error")}

@app.get("/api/v1/forecasts/{forecast_id}/details")
def get_forecast_results(forecast_id: str):
    if forecast_id not in forecasts_results:
        raise HTTPException(
            status_code=404, 
            detail="Hasil belum siap atau tidak ditemukan"
        )
    return forecasts_results[forecast_id]

@app.get("/api/v1/pipeline/outliers")
def get_pipeline_outliers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    path = os.path.join(base_dir, "processed_data", "outlier_summary.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df.to_dict(orient="records")
    return []

@app.get("/api/v1/pipeline/events")
def get_pipeline_events():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    path = os.path.join(base_dir, "processed_data", "time_series_global.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(0)
        
        promo_avg = df[df['is_promo'] == 1]['y'].mean() if 'is_promo' in df.columns else 0
        normal_avg = df[df['is_promo'] == 0]['y'].mean() if 'is_promo' in df.columns else 0
        holiday_avg = df[df['is_holiday'] == 1]['y'].mean() if 'is_holiday' in df.columns else 0
        
        return {
            "promo_impact": {"promo": promo_avg, "normal": normal_avg},
            "holiday_impact": {"holiday": holiday_avg}
        }
    return {}

@app.get("/api/v1/pipeline/monthly")
def get_pipeline_monthly():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    path = os.path.join(base_dir, "processed_data", "time_series_category_monthly.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df_grouped = df.groupby('ds')['y'].sum().reset_index()
        return df_grouped.tail(12).to_dict(orient="records")
    return []

@app.get("/api/v1/pipeline/features")
def get_pipeline_features():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # PERBAIKAN: Hapus ".."
    path = os.path.join(base_dir, "processed_data", "time_series_category_feature_engineered.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df_sampled = df.groupby('Category').tail(2)
        return df_sampled.fillna(0).to_dict(orient="records")
    return []

@app.get("/")
def read_root():
    url_frontend_kamu = "https://perpetual-friendship-production.up.railway.app/"
    
    return RedirectResponse(url=url_frontend_kamu)
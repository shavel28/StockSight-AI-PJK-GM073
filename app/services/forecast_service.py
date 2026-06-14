"""
Forecasting service — integrasi Prophet & ARIMA ke API.
Dipanggil sebagai BackgroundTask agar tidak blocking endpoint.
"""
from datetime import date

import holidays as hol
import numpy as np
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Forecast, ForecastDetail, SalesRecord, Product


# ── Helper: ambil data sales global per upload dari DB ──────────
async def _get_global_sales_df(db: AsyncSession, upload_id: str) -> pd.DataFrame:
    result = await db.execute(
        select(
            SalesRecord.sale_date,
            func.sum(SalesRecord.quantity_sold).label("quantity_sold"),
            func.max(SalesRecord.is_holiday).label("is_holiday"),
            func.max(SalesRecord.is_payday).label("is_payday"),
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .where(Product.upload_id == upload_id)
        .group_by(SalesRecord.sale_date)
        .order_by(SalesRecord.sale_date)
    )
    records = result.fetchall()

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "ds": r[0],
        "y": r[1],
        "is_holiday": r[2] if r[2] is not None else 0,
        "is_payday": r[3] if r[3] is not None else 0,
    } for r in records])

    df["ds"] = pd.to_datetime(df["ds"])
    return df


# ── Helper: buat holiday dataframe untuk Indonesia ───
def _get_id_holidays(years: list[int]) -> pd.DataFrame:
    id_hol = hol.Indonesia(years=years)
    rows = [{"ds": pd.Timestamp(d), "holiday": name} for d, name in id_hol.items()]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["ds", "holiday"])


# ── Evaluasi model (MAPE & RMSE) ─────────────────────
def _evaluate(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float]:
    mask = actual != 0
    mape = float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    return round(mape, 4), round(rmse, 4)


# ── Prophet ───────────────────────────────────────────
def _run_prophet(df: pd.DataFrame, horizon: int, include_holidays: bool) -> dict:
    from app.services.model_registry import get_prophet_model
    import logging

    logger = logging.getLogger(__name__)

    # Lengkapi kolom jika tidak ada
    if "is_holiday" not in df.columns:
        df["is_holiday"] = 0
    else:
        df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)

    if "is_payday" not in df.columns:
        df["is_payday"] = 0
    else:
        df["is_payday"] = df["is_payday"].fillna(0).astype(int)

    train = df.iloc[: -min(30, len(df) // 5)].copy()
    val = df.iloc[len(train):].copy()

    # Ambil model pre-trained dari registry
    model = get_prophet_model()
    is_pretrained = model is not None

    if is_pretrained:
        logger.info("Menggunakan model Prophet pra-latih (Notebooks/prophet_model.json) dari registry.")
    else:
        logger.info("Model pra-latih tidak tersedia. Melatih model Prophet baru dari awal.")
        from prophet import Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.80,
        )
        has_holiday = include_holidays
        has_payday = True

        if has_holiday:
            model.add_regressor("is_holiday")
        if has_payday:
            model.add_regressor("is_payday")

        model.fit(train)

    # Evaluasi pada validation set
    if len(val) > 0:
        val_future = val[["ds"]].copy()
        # Secara dinamis masukkan regressor yang diharapkan oleh model (misal: is_holiday)
        for regressor in model.extra_regressors.keys():
            if regressor in val.columns:
                val_future[regressor] = val[regressor].fillna(0).astype(int)
            else:
                val_future[regressor] = 0
        
        val_pred = model.predict(val_future)
        mape, rmse = _evaluate(val["y"].values, val_pred["yhat"].values)
    else:
        mape, rmse = None, None

    # Forecast ke depan mulai dari tanggal terakhir pada data sales
    last_date = df["ds"].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
    future = pd.DataFrame({"ds": future_dates})

    # Hitung dinamis untuk tanggal di masa depan
    for regressor in model.extra_regressors.keys():
        future[regressor] = np.nan
        nan_mask = future[regressor].isna()
        if nan_mask.any():
            future_dates_series = future.loc[nan_mask, "ds"]
            
            if regressor == "is_holiday":
                years = future_dates_series.dt.year.dropna().unique().tolist()
                if years:
                    id_hol = hol.Indonesia(years=years)
                    holiday_dates = set(id_hol.keys())
                    future.loc[nan_mask, "is_holiday"] = future_dates_series.dt.date.isin(holiday_dates).astype(int)
                else:
                    future.loc[nan_mask, "is_holiday"] = 0
                    
            elif regressor == "is_payday":
                day = future_dates_series.dt.day
                future.loc[nan_mask, "is_payday"] = ((day <= 5) | (day >= 25)).astype(int)
                
            else:
                future.loc[nan_mask, regressor] = 0

        future[regressor] = future[regressor].fillna(0).astype(int)

    forecast = model.predict(future)
    future_only = forecast.copy()

    details = [
        {
            "forecast_date": row["ds"].date(),
            "predicted_qty": max(0.0, round(row["yhat"], 2)),
            "lower_bound": max(0.0, round(row["yhat_lower"], 2)),
            "upper_bound": max(0.0, round(row["yhat_upper"], 2)),
        }
        for _, row in future_only.iterrows()
    ]
    return {"mape": mape, "rmse": rmse, "details": details}


# ── ARIMA ─────────────────────────────────────────────
def _run_arima(df: pd.DataFrame, horizon: int) -> dict:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    # Tentukan apakah fitur eksternal ada
    has_exog = "is_holiday" in df.columns and "is_payday" in df.columns
    exog_cols = ["is_holiday", "is_payday"]

    # Align ke frekuensi harian (D) dan isi nilai kosong
    df_aligned = df.set_index("ds").asfreq("D").fillna({
        "y": 0,
        "is_holiday": 0,
        "is_payday": 0
    })

    series = df_aligned["y"]
    exog = df_aligned[exog_cols] if has_exog else None

    # Pembagian data latih dan validasi
    train_len = len(series) - min(30, len(series) // 5)
    train_y = series.iloc[:train_len]
    val_y = series.iloc[train_len:]

    train_exog = exog.iloc[:train_len] if has_exog else None
    val_exog = exog.iloc[train_len:] if has_exog else None

    model = SARIMAX(
        train_y,
        exog=train_exog,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 0, 7),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    result = model.fit(disp=False)

    # Evaluasi dengan data validasi
    if len(val_y) > 0:
        val_pred = result.predict(start=train_len, end=len(series) - 1, exog=val_exog)
        mape, rmse = _evaluate(val_y.values, val_pred.values)
    else:
        mape, rmse = None, None

    # Buat indeks tanggal masa depan
    last_date = series.index.max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

    # Siapkan exog untuk prediksi masa depan secara dinamis
    if has_exog:
        future_exog = pd.DataFrame(index=future_dates)
        years = future_dates.year.dropna().unique().tolist()
        if years:
            id_hol = hol.Indonesia(years=years)
            holiday_dates = set(id_hol.keys())
            future_exog["is_holiday"] = pd.Index(future_exog.index.date).isin(holiday_dates).astype(int)
        else:
            future_exog["is_holiday"] = 0

        future_exog["is_payday"] = ((future_exog.index.day <= 5) | (future_exog.index.day >= 25)).astype(int)
    else:
        future_exog = None

    forecast = result.forecast(steps=horizon, exog=future_exog)
    conf = result.get_forecast(steps=horizon, exog=future_exog).conf_int(alpha=0.20)

    details = []
    for i, (idx, val_f) in enumerate(forecast.items()):
        details.append({
            "forecast_date": idx.date() if hasattr(idx, "date") else idx,
            "predicted_qty": max(0.0, round(float(val_f), 2)),
            "lower_bound": max(0.0, round(float(conf.iloc[i, 0]), 2)),
            "upper_bound": max(0.0, round(float(conf.iloc[i, 1]), 2)),
        })
    return {"mape": mape, "rmse": rmse, "details": details}


# ── Entry point (background task) ─────────────────────
async def run_forecast(
    forecast_id: str,
    upload_id: str,
    horizon_days: int,
    model_name: str,
    include_holidays: bool,
):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        forecast = await db.get(Forecast, forecast_id)
        if not forecast:
            return

        try:
            forecast.status = "running"
            await db.commit()

            df = await _get_global_sales_df(db, upload_id)
            if df.empty or len(df) < 10:
                raise ValueError("Data penjualan terlalu sedikit untuk forecasting (minimal 10 hari)")

            if model_name == "prophet":
                result = _run_prophet(df, horizon_days, include_holidays)
            elif model_name == "arima":
                result = _run_arima(df, horizon_days)
            else:
                raise ValueError(f"Model tidak dikenali: {model_name}")

            forecast.mape = result["mape"]
            forecast.rmse = result["rmse"]
            forecast.status = "done"
            await db.flush()

            detail_objs = [
                ForecastDetail(
                    forecast_id=forecast_id,
                    forecast_date=d["forecast_date"],
                    predicted_qty=d["predicted_qty"],
                    lower_bound=d["lower_bound"],
                    upper_bound=d["upper_bound"],
                )
                for d in result["details"]
            ]
            db.add_all(detail_objs)
            await db.commit()

        except Exception as e:
            await db.rollback()
            forecast.status = "error"
            await db.commit()
            raise e


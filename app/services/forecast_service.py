"""
Forecasting service — integrasi Prophet & ARIMA ke API.
Dipanggil sebagai BackgroundTask agar tidak blocking endpoint.
"""
from datetime import date

import holidays as hol
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Forecast, ForecastDetail, SalesRecord


# ── Helper: ambil data sales dari DB ─────────────────
async def _get_sales_df(db: AsyncSession, product_id: str) -> pd.DataFrame:
    result = await db.execute(
        select(SalesRecord)
        .where(SalesRecord.product_id == product_id)
        .order_by(SalesRecord.sale_date)
    )
    records = result.scalars().all()

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "ds": r.sale_date,
        "y": r.quantity_sold,
    } for r in records])

    df["ds"] = pd.to_datetime(df["ds"])
    # Agregasi harian (jika ada lebih dari 1 transaksi per hari)
    df = df.groupby("ds", as_index=False)["y"].sum()
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
    from prophet import Prophet

    train = df.iloc[: -min(30, len(df) // 5)]
    val = df.iloc[len(train):]

    holiday_df = None
    if include_holidays:
        years = sorted(df["ds"].dt.year.unique().tolist())
        holiday_df = _get_id_holidays(years + [max(years) + 1])

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        holidays=holiday_df,
        interval_width=0.80,
    )
    model.fit(train)

    # Evaluasi pada validation set
    if len(val) > 0:
        val_future = model.make_future_dataframe(periods=0)
        val_future = val_future[val_future["ds"].isin(val["ds"])]
        val_pred = model.predict(val_future)
        mape, rmse = _evaluate(val["y"].values, val_pred["yhat"].values)
    else:
        mape, rmse = None, None

    # Forecast ke depan
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)
    future_only = forecast[forecast["ds"] > df["ds"].max()].copy()

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

    series = df.set_index("ds")["y"].asfreq("D").fillna(0)
    train = series.iloc[: -min(30, len(series) // 5)]
    val = series.iloc[len(train):]

    model = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 0, 7),
                    enforce_stationarity=False, enforce_invertibility=False)
    result = model.fit(disp=False)

    if len(val) > 0:
        val_pred = result.predict(start=len(train), end=len(train) + len(val) - 1)
        mape, rmse = _evaluate(val.values, val_pred.values)
    else:
        mape, rmse = None, None

    forecast = result.forecast(steps=horizon)
    conf = result.get_forecast(steps=horizon).conf_int(alpha=0.20)

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
    product_id: str,
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

            df = await _get_sales_df(db, product_id)
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


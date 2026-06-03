from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import Forecast, ForecastDetail, Product, Upload
from app.schemas.schemas import ForecastOut, ForecastRequest, ForecastWithDetails
from app.services.forecast_service import run_forecast

router = APIRouter(prefix="/forecasts", tags=["Forecasting"])

VALID_HORIZONS = {30, 60, 90}
VALID_MODELS = {"prophet", "arima"}


@router.post("", response_model=ForecastOut, status_code=202)
async def create_forecast(
    payload: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.horizon_days not in VALID_HORIZONS:
        raise HTTPException(400, f"horizon_days harus salah satu dari {VALID_HORIZONS}")
    if payload.model not in VALID_MODELS:
        raise HTTPException(400, f"model harus salah satu dari {VALID_MODELS}")

    # Pastikan produk milik user
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(404, "Produk tidak ditemukan")
    upload = await db.get(Upload, product.upload_id)
    if not upload or upload.user_id != current_user.id:
        raise HTTPException(403, "Akses ditolak")

    forecast = Forecast(
        product_id=payload.product_id,
        model_used=payload.model,
        horizon_days=payload.horizon_days,
        status="pending",
    )
    db.add(forecast)
    await db.flush()

    background_tasks.add_task(
        run_forecast, forecast.id, payload.product_id,
        payload.horizon_days, payload.model, payload.include_holidays,
    )
    return forecast



@router.get("", response_model=list[ForecastOut])
async def list_forecasts(
    product_id: Optional[str] = Query(None),
    horizon: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(Forecast)
        .join(Product, Forecast.product_id == Product.id)
        .join(Upload, Product.upload_id == Upload.id)
        .where(Upload.user_id == current_user.id)
        .order_by(Forecast.generated_at.desc())
    )
    if product_id:
        q = q.where(Forecast.product_id == product_id)
    if horizon:
        q = q.where(Forecast.horizon_days == horizon)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{forecast_id}", response_model=ForecastOut)
async def get_forecast(
    forecast_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    forecast = await db.get(Forecast, forecast_id)
    if not forecast:
        raise HTTPException(404, "Forecast tidak ditemukan")
    return forecast


@router.get("/{forecast_id}/details", response_model=ForecastWithDetails)
async def get_forecast_details(
    forecast_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    forecast = await db.get(Forecast, forecast_id)
    if not forecast:
        raise HTTPException(404, "Forecast tidak ditemukan")
    if forecast.status != "done":
        raise HTTPException(400, f"Forecast belum selesai. Status: {forecast.status}")

    result = await db.execute(
        select(ForecastDetail)
        .where(ForecastDetail.forecast_id == forecast_id)
        .order_by(ForecastDetail.forecast_date)
    )
    details = result.scalars().all()
    return {**forecast.__dict__, "details": details}

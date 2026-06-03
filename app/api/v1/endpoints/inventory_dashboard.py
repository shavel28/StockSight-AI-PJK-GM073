from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import (
    Forecast, InventoryAlert, Product, SalesRecord, Upload
)
from app.schemas.schemas import (
    AlertOut, DashboardSummary, ReorderInfo, TopProduct
)
from app.services.inventory_service import calculate_reorder

# ── Inventory Router ──────────────────────────────────
inventory_router = APIRouter(prefix="/inventory", tags=["Inventory & Alerts"])


@inventory_router.get("/reorder", response_model=list[ReorderInfo])
async def get_reorder_info(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Product)
        .join(Upload, Product.upload_id == Upload.id)
        .where(Upload.user_id == current_user.id)
    )
    products = result.scalars().all()
    infos = []
    for p in products:
        info = await calculate_reorder(db, p.id)
        if "error" not in info:
            infos.append(ReorderInfo(**info))
    return infos


@inventory_router.get("/alerts", response_model=list[AlertOut])
async def get_alerts(
    active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(InventoryAlert)
        .join(Product, InventoryAlert.product_id == Product.id)
        .join(Upload, Product.upload_id == Upload.id)
        .where(Upload.user_id == current_user.id)
        .order_by(InventoryAlert.triggered_at.desc())
    )
    if active is not None:
        q = q.where(InventoryAlert.is_active == active)
    result = await db.execute(q)
    return result.scalars().all()


@inventory_router.patch("/alerts/{alert_id}", response_model=AlertOut)
async def dismiss_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    alert = await db.get(InventoryAlert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert tidak ditemukan")
    alert.is_active = False
    return alert


# ── Dashboard Router ──────────────────────────────────
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Total produk
    total_products_res = await db.execute(
        select(func.count(Product.id))
        .join(Upload).where(Upload.user_id == current_user.id)
    )
    total_products = total_products_res.scalar() or 0

    # Alert aktif
    active_alerts_res = await db.execute(
        select(func.count(InventoryAlert.id))
        .join(Product).join(Upload)
        .where(Upload.user_id == current_user.id, InventoryAlert.is_active == True)
    )
    active_alerts = active_alerts_res.scalar() or 0

    # Jumlah upload
    uploads_res = await db.execute(
        select(func.count(Upload.id)).where(Upload.user_id == current_user.id)
    )
    uploads_count = uploads_res.scalar() or 0

    # Rata-rata MAPE
    mape_res = await db.execute(
        select(func.avg(Forecast.mape))
        .join(Product).join(Upload)
        .where(Upload.user_id == current_user.id, Forecast.status == "done")
    )
    avg_mape = mape_res.scalar()

    return DashboardSummary(
        total_products=total_products,
        active_alerts=active_alerts,
        uploads_count=uploads_count,
        avg_mape=round(avg_mape, 2) if avg_mape else None,
    )


@dashboard_router.get("/top-products", response_model=list[TopProduct])
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(
            Product.id,
            Product.product_name,
            Product.category,
            func.sum(SalesRecord.quantity_sold).label("total_sold"),
        )
        .join(SalesRecord, Product.id == SalesRecord.product_id)
        .join(Upload, Product.upload_id == Upload.id)
        .where(Upload.user_id == current_user.id)
        .group_by(Product.id, Product.product_name, Product.category)
        .order_by(func.sum(SalesRecord.quantity_sold).desc())
        .limit(limit)
    )
    return [
        TopProduct(
            product_id=str(row.id),
            product_name=row.product_name,
            total_sold=row.total_sold,
            category=row.category,
        )
        for row in result.all()
    ]

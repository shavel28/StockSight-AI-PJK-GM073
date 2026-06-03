from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import Product, SalesRecord, Upload
from app.schemas.schemas import ProductOut, SalesRecordOut, StockUpdate

router = APIRouter(prefix="/products", tags=["Products"])


async def _owned_product(product_id: str, db: AsyncSession, user_id: str) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Produk tidak ditemukan")
    upload = await db.get(Upload, product.upload_id)
    if not upload or upload.user_id != user_id:
        raise HTTPException(403, "Akses ditolak")
    return product


@router.get("", response_model=list[ProductOut])
async def list_products(
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Ambil semua produk dari upload milik user
    q = (
        select(Product)
        .join(Upload, Product.upload_id == Upload.id)
        .where(Upload.user_id == current_user.id, Upload.status == "done")
    )
    if category:
        q = q.where(Product.category == category)
    if region:
        q = q.where(Product.region == region)

    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await _owned_product(product_id, db, current_user.id)


@router.get("/{product_id}/sales", response_model=list[SalesRecordOut])
async def get_sales(
    product_id: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await _owned_product(product_id, db, current_user.id)
    q = select(SalesRecord).where(SalesRecord.product_id == product_id)
    if from_date:
        q = q.where(SalesRecord.sale_date >= from_date)
    if to_date:
        q = q.where(SalesRecord.sale_date <= to_date)
    q = q.order_by(SalesRecord.sale_date)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def update_stock(
    product_id: str,
    payload: StockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = await _owned_product(product_id, db, current_user.id)
    product.current_stock = payload.current_stock

    from app.services.inventory_service import trigger_alert_if_needed
    await trigger_alert_if_needed(db, product_id)

    return product

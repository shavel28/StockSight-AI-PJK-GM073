"""
Reorder point & safety stock calculation.
Formula standar inventory management:
  Safety Stock = Z * σ_demand * √lead_time
  Reorder Point = (avg_demand * lead_time) + safety_stock
"""
import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Product, SalesRecord, InventoryAlert


LEAD_TIME_DAYS = 7      # asumsi lead time supplier 7 hari
Z_SCORE = 1.65          # 95% service level


async def calculate_reorder(db: AsyncSession, product_id: str) -> dict:
    result = await db.execute(
        select(SalesRecord.quantity_sold)
        .where(SalesRecord.product_id == product_id)
    )
    quantities = [r[0] for r in result.fetchall()]

    if len(quantities) < 7:
        return {
            "product_id": product_id,
            "reorder_point": None,
            "safety_stock": None,
            "needs_reorder": False,
            "error": "Data historis kurang dari 7 hari",
        }

    avg_demand = sum(quantities) / len(quantities)
    std_demand = math.sqrt(sum((q - avg_demand) ** 2 for q in quantities) / len(quantities))

    safety_stock = round(Z_SCORE * std_demand * math.sqrt(LEAD_TIME_DAYS), 2)
    reorder_point = round((avg_demand * LEAD_TIME_DAYS) + safety_stock, 2)

    product = await db.get(Product, product_id)
    needs_reorder = product.current_stock <= reorder_point if product else False

    return {
        "product_id": product_id,
        "product_name": product.product_name if product else "",
        "current_stock": product.current_stock if product else 0,
        "reorder_point": reorder_point,
        "safety_stock": safety_stock,
        "needs_reorder": needs_reorder,
    }


async def trigger_alert_if_needed(db: AsyncSession, product_id: str):
    """Buat atau update alert jika stok di bawah reorder point."""
    info = await calculate_reorder(db, product_id)
    if not info.get("reorder_point"):
        return

    product = await db.get(Product, product_id)
    if not product:
        return

    stock = product.current_stock
    rp = info["reorder_point"]
    ss = info["safety_stock"]

    alert_type = None
    if stock <= ss:
        alert_type = "critical"
    elif stock <= rp:
        alert_type = "reorder"

    if alert_type:
        # Nonaktifkan alert lama
        old = await db.execute(
            select(InventoryAlert).where(
                InventoryAlert.product_id == product_id,
                InventoryAlert.is_active == True,
            )
        )
        for a in old.scalars():
            a.is_active = False

        alert = InventoryAlert(
            product_id=product_id,
            alert_type=alert_type,
            reorder_point=rp,
            safety_stock=ss,
            is_active=True,
        )
        db.add(alert)
        await db.flush()

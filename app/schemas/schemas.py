from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Upload ────────────────────────────────────────────
class UploadOut(BaseModel):
    id: str
    filename: str
    status: str
    error_message: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────
class ProductOut(BaseModel):
    id: str
    product_name: str
    category: Optional[str]
    region: Optional[str]
    current_stock: int
    created_at: datetime

    class Config:
        from_attributes = True


class StockUpdate(BaseModel):
    current_stock: int


# ── Sales ─────────────────────────────────────────────
class SalesRecordOut(BaseModel):
    id: str
    sale_date: date
    quantity_sold: int
    revenue: Optional[float]
    is_holiday: Optional[int] = 0
    is_payday: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Forecast ──────────────────────────────────────────
class ForecastRequest(BaseModel):
    product_id: str
    horizon_days: int = 30          # 30 | 60 | 90
    model: str = "prophet"          # prophet | arima
    include_holidays: bool = True


class ForecastOut(BaseModel):
    id: str
    product_id: str
    model_used: str
    horizon_days: int
    mape: Optional[float]
    rmse: Optional[float]
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True


class ForecastDetailOut(BaseModel):
    forecast_date: date
    predicted_qty: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]

    class Config:
        from_attributes = True


class ForecastWithDetails(ForecastOut):
    details: List[ForecastDetailOut] = []


# ── Inventory / Alert ─────────────────────────────────
class ReorderInfo(BaseModel):
    product_id: str
    product_name: str
    current_stock: int
    reorder_point: float
    safety_stock: float
    needs_reorder: bool


class AlertOut(BaseModel):
    id: str
    product_id: str
    alert_type: str
    reorder_point: Optional[float]
    safety_stock: Optional[float]
    is_active: bool
    triggered_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────
class DashboardSummary(BaseModel):
    total_products: int
    active_alerts: int
    uploads_count: int
    avg_mape: Optional[float]


class TopProduct(BaseModel):
    product_id: str
    product_name: str
    total_sold: int
    category: Optional[str]

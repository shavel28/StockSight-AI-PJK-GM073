import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user | admin
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="user", cascade="all, delete")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(20), default="pending")  # pending | processing | done | error
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploads")
    products = relationship("Product", back_populates="upload", cascade="all, delete")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    upload_id = Column(UUID(as_uuid=False), ForeignKey("uploads.id", ondelete="CASCADE"))
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    current_stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="products")
    sales_records = relationship("SalesRecord", back_populates="product", cascade="all, delete")
    forecasts = relationship("Forecast", back_populates="product", cascade="all, delete")
    alerts = relationship("InventoryAlert", back_populates="product", cascade="all, delete")


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id = Column(UUID(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"))
    sale_date = Column(Date, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=True)

    product = relationship("Product", back_populates="sales_records")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id = Column(UUID(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"))
    model_used = Column(String(20), nullable=False)  # prophet | arima
    horizon_days = Column(Integer, nullable=False)   # 30 | 60 | 90
    mape = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    status = Column(String(20), default="pending")   # pending | running | done | error
    generated_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="forecasts")
    details = relationship("ForecastDetail", back_populates="forecast", cascade="all, delete")


class ForecastDetail(Base):
    __tablename__ = "forecast_details"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    forecast_id = Column(UUID(as_uuid=False), ForeignKey("forecasts.id", ondelete="CASCADE"))
    forecast_date = Column(Date, nullable=False)
    predicted_qty = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)

    forecast = relationship("Forecast", back_populates="details")


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id = Column(UUID(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"))
    alert_type = Column(String(30), nullable=False)  # critical | warning | reorder
    reorder_point = Column(Float, nullable=True)
    safety_stock = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="alerts")

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat tabel dan folder upload saat startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Pastikan kolom is_holiday dan is_payday ada di tabel sales_records
        await conn.execute(text("ALTER TABLE sales_records ADD COLUMN IF NOT EXISTS is_holiday INTEGER DEFAULT 0;"))
        await conn.execute(text("ALTER TABLE sales_records ADD COLUMN IF NOT EXISTS is_payday INTEGER DEFAULT 0;"))
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="StockSight AI — API",
    description="AI-Powered Demand Forecasting & Inventory Dashboard for UMKM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-stocksight.vercel.app/"],   # Ganti dengan domain frontend saat production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "StockSight AI API"}


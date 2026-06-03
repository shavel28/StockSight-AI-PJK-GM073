from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.forecasts import router as forecasts_router
from app.api.v1.endpoints.inventory_dashboard import (
    inventory_router,
    dashboard_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(uploads_router)
api_router.include_router(products_router)
api_router.include_router(forecasts_router)
api_router.include_router(inventory_router)
api_router.include_router(dashboard_router)

from backend.api.routes.health import router as health_router
from fastapi import APIRouter


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)

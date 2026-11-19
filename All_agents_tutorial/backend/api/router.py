from backend.api.routes.investigation import router as investigation_router
from fastapi import APIRouter


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(investigation_router)

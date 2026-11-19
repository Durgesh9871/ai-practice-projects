
from fastapi import APIRouter

from backend.schema.health import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/" , response_model=HealthService)
def health() -> HealthService:
    return HealthService(status=True, service={"redis": True})  
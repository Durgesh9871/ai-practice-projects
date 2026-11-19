


from pydantic import BaseModel
from typing import Any

class HealthService(BaseModel):
    status: bool
    service: dict[str, Any]

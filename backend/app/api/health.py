from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.version import VERSION

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    mode: str
    env: str
    time_utc: datetime


@router.get("/healthz", response_model=HealthStatus)
def healthz(settings: Annotated[Settings, Depends(get_settings)]) -> HealthStatus:
    return HealthStatus(
        status="ok",
        service="prahari-api",
        version=VERSION,
        mode=settings.mode,
        env=settings.env,
        time_utc=datetime.now(UTC),
    )

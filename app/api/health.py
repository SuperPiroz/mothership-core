from datetime import datetime, timezone

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app import __version__
from app.config import get_settings
from app.database import check_database_health

router = APIRouter(tags=["Health"])
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    database: dict[str, str | bool]


@router.get("/healthz", response_model=HealthResponse, summary="Liveness Probe")
async def healthz():
    """Liveness probe: verifies that the process is alive and accepting connections."""
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=__version__,
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    responses={
        200: {"description": "Service and all dependencies are healthy"},
        503: {"description": "Service dependency (e.g. database) is unhealthy"},
    },
)
async def readyz(response: Response):
    """Readiness probe: verifies that database and required dependencies are operational."""
    db_ok, db_msg = await check_database_health()
    now = datetime.now(timezone.utc)

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="unhealthy",
            service=settings.PROJECT_NAME,
            version=__version__,
            timestamp=now,
            database={"healthy": False, "message": db_msg},
        )

    return ReadinessResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=__version__,
        timestamp=now,
        database={"healthy": True, "message": db_msg},
    )

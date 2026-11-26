from fastapi import APIRouter

from app.api.v1.incidents import router as incidents_router
from app.api.v1.services import router as services_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(services_router)
api_v1_router.include_router(incidents_router)

__all__ = ["api_v1_router"]

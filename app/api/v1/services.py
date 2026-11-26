import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from app.services import service_catalog

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=list[ServiceResponse], summary="List all services")
async def list_services(
    category: str | None = Query(default=None, description="Filter by category"),
    is_monitored: bool | None = Query(default=None, description="Filter by monitoring status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List services registered in the homelab service catalog."""
    return await service_catalog.get_services(
        db, category=category, is_monitored=is_monitored, skip=skip, limit=limit
    )


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new service",
)
async def register_service(
    service_in: ServiceCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a new service to the catalog."""
    # Check if slug or name already exists
    slug = service_in.slug or service_catalog.generate_slug(service_in.name)
    existing = await service_catalog.get_service_by_slug(db, slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service with slug '{slug}' already exists",
        )
    return await service_catalog.create_service(db, service_in)


@router.get("/{service_id}", response_model=ServiceResponse, summary="Get service by ID")
async def get_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a single service by UUID."""
    service = await service_catalog.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return service


@router.put("/{service_id}", response_model=ServiceResponse, summary="Update service")
async def update_service(
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update metadata for an existing service."""
    service = await service_catalog.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return await service_catalog.update_service(db, service, service_in)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete service",
)
async def delete_service(
    service_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a service from the catalog."""
    service = await service_catalog.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    await service_catalog.delete_service(db, service)

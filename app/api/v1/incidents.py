import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=list[IncidentResponse], summary="List incidents")
async def list_incidents(
    service_id: uuid.UUID | None = Query(default=None, description="Filter by service"),
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status"),
    severity: str | None = Query(default=None, description="Filter by severity"),
    search: str | None = Query(default=None, description="Search in title or description"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List and search incident and maintenance logs."""
    return await incident_service.get_incidents(
        db,
        service_id=service_id,
        status=status_filter,
        severity=severity,
        search=search,
        skip=skip,
        limit=limit,
    )


# ==============================================================================
# OWASP SÅRBARHETSDEMONSTRATION (FÖR SECURE DEVOPS STEG 1 - DEMO BRANCH ENBART)
# ==============================================================================


@router.get(
    "/demo/vulnerable-search",
    summary="[OWASP DEMO A03] Vulnerable search via raw SQL string concatenation",
)
async def vulnerable_search(
    q: str = Query(..., description="Unsanitized raw search query"),
    db: AsyncSession = Depends(get_db),
):
    """
    DEMO ONLY: Vulnerable to SQL Injection (OWASP A03:2021).
    Direct string interpolation into raw SQL without parameterization.
    Exploit with payload: test' OR '1'='1
    """
    raw_query = (
        "SELECT id, title, description, severity, status "
        f"FROM incidents WHERE title LIKE '%{q}%'"
    )
    result = await db.execute(text(raw_query))
    rows = result.mappings().all()
    return [dict(row) for row in rows]


@router.delete(
    "/demo/insecure-delete/{incident_id}",
    summary="[OWASP DEMO A01] Insecure delete without authorization check (IDOR)",
)
async def insecure_delete(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    DEMO ONLY: Vulnerable to Broken Access Control / IDOR (OWASP A01:2021).
    Allows any unauthenticated user to delete arbitrary incidents by ID.
    """
    incident = await incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    await incident_service.delete_incident(db, incident)
    return {"message": "Incident deleted without authorization check"}


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
)
async def create_incident(
    incident_in: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a new incident or service disruption."""
    return await incident_service.create_incident(db, incident_in)


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Get incident by ID")
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single incident by UUID."""
    incident = await incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident


@router.put("/{incident_id}", response_model=IncidentResponse, summary="Update incident")
async def update_incident(
    incident_id: uuid.UUID,
    incident_in: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an incident (e.g. status transition or resolution)."""
    incident = await incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return await incident_service.update_incident(db, incident, incident_in)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete incident",
)
async def delete_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an incident log entry."""
    incident = await incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    await incident_service.delete_incident(db, incident)

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


async def get_incidents(
    db: AsyncSession,
    service_id: uuid.UUID | None = None,
    status: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Incident]:
    """Retrieve incidents with optional status, severity, and parameterized text search."""
    query = select(Incident)

    if service_id:
        query = query.where(Incident.service_id == service_id)
    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if search:
        search_filter = f"%{search}%"
        # Safe parameterized search preventing SQL injection
        query = query.where(
            or_(
                Incident.title.ilike(search_filter),
                Incident.description.ilike(search_filter),
            )
        )

    query = query.offset(skip).limit(limit).order_by(Incident.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_incident_by_id(db: AsyncSession, incident_id: uuid.UUID) -> Incident | None:
    """Retrieve an incident by its UUID."""
    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_incident(
    db: AsyncSession,
    incident_in: IncidentCreate,
    created_by_user_id: uuid.UUID | None = None,
) -> Incident:
    """Create a new incident log entry."""
    db_incident = Incident(
        title=incident_in.title,
        description=incident_in.description,
        severity=incident_in.severity,
        status=incident_in.status,
        service_id=incident_in.service_id,
        resolution=incident_in.resolution,
        created_by_user_id=created_by_user_id,
    )
    if incident_in.status == "resolved":
        db_incident.resolved_at = datetime.now(timezone.utc)

    db.add(db_incident)
    await db.flush()
    await db.refresh(db_incident)
    return db_incident


async def update_incident(
    db: AsyncSession,
    db_incident: Incident,
    incident_in: IncidentUpdate,
) -> Incident:
    """Update an existing incident."""
    update_data = incident_in.model_dump(exclude_unset=True)

    if update_data.get("status") == "resolved" and db_incident.status != "resolved":
        db_incident.resolved_at = datetime.now(timezone.utc)
    elif update_data.get("status") in ["open", "investigating"]:
        db_incident.resolved_at = None

    for field, value in update_data.items():
        setattr(db_incident, field, value)

    await db.flush()
    await db.refresh(db_incident)
    return db_incident


async def delete_incident(db: AsyncSession, db_incident: Incident) -> None:
    """Delete an incident."""
    await db.delete(db_incident)
    await db.flush()

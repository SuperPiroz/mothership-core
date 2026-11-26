import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import ServiceItem
from app.schemas.service import ServiceCreate, ServiceUpdate


def generate_slug(name: str) -> str:
    """Generate a URL-safe lowercase slug from a service name."""
    slug = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)


async def get_services(
    db: AsyncSession,
    category: str | None = None,
    is_monitored: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ServiceItem]:
    """Retrieve all services with optional filtering."""
    query = select(ServiceItem)
    if category:
        query = query.where(ServiceItem.category == category)
    if is_monitored is not None:
        query = query.where(ServiceItem.is_monitored == is_monitored)
    query = query.offset(skip).limit(limit).order_by(ServiceItem.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_service_by_id(db: AsyncSession, service_id: uuid.UUID) -> ServiceItem | None:
    """Retrieve a single service by its UUID."""
    query = select(ServiceItem).where(ServiceItem.id == service_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_service_by_slug(db: AsyncSession, slug: str) -> ServiceItem | None:
    """Retrieve a single service by its unique slug."""
    query = select(ServiceItem).where(ServiceItem.slug == slug)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_service(db: AsyncSession, service_in: ServiceCreate) -> ServiceItem:
    """Create a new service in the catalog."""
    slug = service_in.slug or generate_slug(service_in.name)
    db_service = ServiceItem(
        name=service_in.name,
        slug=slug,
        description=service_in.description,
        category=service_in.category,
        runtime=service_in.runtime,
        internal_url=service_in.internal_url,
        public_url=service_in.public_url,
        health_url=service_in.health_url,
        tags=service_in.tags,
        is_monitored=service_in.is_monitored,
    )
    db.add(db_service)
    await db.flush()
    await db.refresh(db_service)
    return db_service


async def update_service(
    db: AsyncSession,
    db_service: ServiceItem,
    service_in: ServiceUpdate,
) -> ServiceItem:
    """Update an existing service in the catalog."""
    update_data = service_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        update_data["slug"] = generate_slug(update_data["name"])

    for field, value in update_data.items():
        setattr(db_service, field, value)

    await db.flush()
    await db.refresh(db_service)
    return db_service


async def delete_service(db: AsyncSession, db_service: ServiceItem) -> None:
    """Delete a service from the catalog."""
    await db.delete(db_service)
    await db.flush()

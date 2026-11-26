import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Service display name")
    description: str | None = Field(default=None, max_length=500)
    category: str = Field(
        default="service",
        max_length=50,
        description="Category (ai, database, web, system)",
    )
    runtime: str = Field(
        default="docker",
        max_length=50,
        description="Runtime (docker, k8s, host, external)",
    )
    internal_url: str | None = Field(default=None, max_length=255)
    public_url: str | None = Field(default=None, max_length=255)
    health_url: str | None = Field(default=None, max_length=255)
    tags: str | None = Field(default=None, max_length=255)
    is_monitored: bool = Field(default=True)


class ServiceCreate(ServiceBase):
    slug: str | None = Field(default=None, max_length=100)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    category: str | None = None
    runtime: str | None = None
    internal_url: str | None = None
    public_url: str | None = None
    health_url: str | None = None
    tags: str | None = None
    is_monitored: bool | None = None


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

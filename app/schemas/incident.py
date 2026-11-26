import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    severity: str = Field(default="medium", description="Severity (low, medium, high, critical)")
    status: str = Field(default="open", description="Status (open, investigating, resolved)")
    service_id: uuid.UUID | None = None
    resolution: str | None = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    service_id: uuid.UUID | None = None
    resolution: str | None = None


class IncidentResponse(IncidentBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    role: str = Field(default="viewer", description="Role (admin or viewer)")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None

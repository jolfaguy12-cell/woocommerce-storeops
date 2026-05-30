from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.models import BuiltInRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr | None = None
    password: str = Field(min_length=10)
    role: BuiltInRole = BuiltInRole.readonly_viewer
    permissions: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=10)
    role: BuiltInRole | None = None
    permissions: list[str] | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    role: BuiltInRole
    permissions: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

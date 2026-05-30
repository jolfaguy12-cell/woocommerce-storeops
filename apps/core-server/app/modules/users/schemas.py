from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.models import BuiltInRole


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    description: str | None
    module: str


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    permissions: list[PermissionRead] = []


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr | None = None
    full_name: str | None = None
    password: str = Field(min_length=10)
    role: BuiltInRole = BuiltInRole.readonly_viewer
    role_id: int | None = None
    permissions: list[str] = Field(default_factory=list)
    must_change_password: bool = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=10)
    role: BuiltInRole | None = None
    role_id: int | None = None
    permissions: list[str] | None = None
    is_active: bool | None = None
    must_change_password: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    full_name: str | None
    role: BuiltInRole
    role_id: int | None
    permissions: list[str]
    is_active: bool
    is_superuser: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

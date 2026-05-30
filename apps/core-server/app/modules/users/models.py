import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Table, Column, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class BuiltInRole(str, enum.Enum):
    super_admin = "super_admin"
    inventory_manager = "inventory_manager"
    sales_manager = "sales_manager"
    readonly_viewer = "readonly_viewer"
    accountant = "accountant"
    purchase_manager = "purchase_manager"
    supplier_manager = "supplier_manager"


ROLE_PERMISSION_DEFAULTS: dict[str, set[str]] = {
    "super_admin": {
        "dashboard.view", "sync.view", "sync.run_full", "sync.run_changed", "products.view",
        "inventory.view", "inventory.manage", "reports.view", "reports.manage", "users.view",
        "users.create", "users.update", "users.delete", "roles.view", "roles.manage",
        "settings.view", "settings.manage", "logs.view",
    },
    "inventory_manager": {"dashboard.view", "sync.view", "sync.run_full", "sync.run_changed", "products.view", "inventory.view", "inventory.manage", "reports.view"},
    "sales_manager": {"dashboard.view", "products.view", "inventory.view", "reports.view"},
    "readonly_viewer": {"dashboard.view", "products.view", "inventory.view", "reports.view"},
    "accountant": {"dashboard.view", "products.view", "inventory.view", "reports.view", "reports.manage"},
    "purchase_manager": {"dashboard.view", "sync.view", "products.view", "inventory.view", "inventory.manage", "reports.view"},
    "supplier_manager": {"dashboard.view", "products.view", "inventory.view", "reports.view"},
}

ALL_PERMISSIONS: dict[str, tuple[str, str]] = {
    "dashboard.view": ("dashboard", "View dashboard"),
    "sync.view": ("sync", "View Sync Center"),
    "sync.run_full": ("sync", "Run full product sync"),
    "sync.run_changed": ("sync", "Run changed-products sync"),
    "products.view": ("products", "View synced products"),
    "inventory.view": ("inventory", "View inventory"),
    "inventory.manage": ("inventory", "Manage inventory settings"),
    "reports.view": ("reports", "View reports"),
    "reports.manage": ("reports", "Manage reports"),
    "users.view": ("users", "View users"),
    "users.create": ("users", "Create users"),
    "users.update": ("users", "Update users"),
    "users.delete": ("users", "Delete/deactivate users"),
    "roles.view": ("roles", "View roles"),
    "roles.manage": ("roles", "Manage roles"),
    "settings.view": ("settings", "View settings"),
    "settings.manage": ("settings", "Manage settings"),
    "logs.view": ("logs", "View logs"),
}

# Backward-compatible alias used by existing routes/docs.
DEFAULT_ROLE_PERMISSIONS = {BuiltInRole(k): v for k, v in ROLE_PERMISSION_DEFAULTS.items() if k in BuiltInRole._value2member_map_}

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(80), index=True)

    roles: Mapped[list[Role]] = relationship(secondary=role_permissions, back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[BuiltInRole] = mapped_column(Enum(BuiltInRole), default=BuiltInRole.readonly_viewer)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role_record: Mapped[Role | None] = relationship()
    audit_logs: Mapped[list["AuditLog"]] = relationship(foreign_keys="AuditLog.user_id", cascade="all, delete-orphan")

    def effective_permissions(self) -> set[str]:
        if self.is_superuser or self.role == BuiltInRole.super_admin:
            return set(ALL_PERMISSIONS.keys())
        role_permissions_set = {permission.code for permission in self.role_record.permissions} if self.role_record else set()
        legacy_permissions = ROLE_PERMISSION_DEFAULTS.get(self.role.value, set())
        return set(self.permissions or []) | role_permissions_set | legacy_permissions


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    module: Mapped[str] = mapped_column(String(80), index=True, default="system")
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

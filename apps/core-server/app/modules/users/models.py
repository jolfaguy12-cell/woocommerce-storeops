import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, func
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


class AuditAction(str, enum.Enum):
    user_created = "user_created"
    user_updated = "user_updated"
    user_deleted = "user_deleted"
    user_deactivated = "user_deactivated"
    login_success = "login_success"
    login_failed = "login_failed"
    role_changed = "role_changed"
    permissions_changed = "permissions_changed"


DEFAULT_ROLE_PERMISSIONS: dict[BuiltInRole, set[str]] = {
    BuiltInRole.super_admin: {
        "inventory.view", "inventory.manage", "inventory.export", "reports.view", "reports.manage",
        "telegram.manage", "users.view", "users.create", "users.update", "users.delete",
        "settings.manage", "logs.view", "modules.manage",
    },
    BuiltInRole.inventory_manager: {"inventory.view", "inventory.manage", "inventory.export", "reports.view"},
    BuiltInRole.sales_manager: {"inventory.view", "reports.view"},
    BuiltInRole.readonly_viewer: {"inventory.view", "reports.view", "logs.view"},
    BuiltInRole.accountant: {"inventory.view", "reports.view", "reports.manage"},
    BuiltInRole.purchase_manager: {"inventory.view", "inventory.manage", "reports.view"},
    BuiltInRole.supplier_manager: {"inventory.view", "reports.view"},
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[BuiltInRole] = mapped_column(Enum(BuiltInRole), default=BuiltInRole.readonly_viewer)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    audit_logs: Mapped[list["AuditLog"]] = relationship(foreign_keys="AuditLog.actor_user_id", cascade="all, delete-orphan")

    def effective_permissions(self) -> set[str]:
        return set(self.permissions or []) | DEFAULT_ROLE_PERMISSIONS.get(self.role, set())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

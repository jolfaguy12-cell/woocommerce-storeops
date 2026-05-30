import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BuiltInRole(str, enum.Enum):
    super_admin = "super_admin"
    inventory_manager = "inventory_manager"
    sales_manager = "sales_manager"
    readonly_viewer = "readonly_viewer"
    accountant = "accountant"
    purchase_manager = "purchase_manager"
    supplier_manager = "supplier_manager"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[BuiltInRole] = mapped_column(Enum(BuiltInRole), default=BuiltInRole.readonly_viewer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

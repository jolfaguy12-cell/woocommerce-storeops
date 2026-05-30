from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SettingValueType(str, enum.Enum):
    string = "string"
    integer = "integer"
    boolean = "boolean"
    float = "float"
    json = "json"
    encrypted_string = "encrypted_string"


class SystemSetting(Base):
    """Runtime/business setting persisted in the Core Server database."""

    __tablename__ = "system_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_system_settings_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    value_type: Mapped[str] = mapped_column(String(40), default=SettingValueType.string.value)
    group: Mapped[str] = mapped_column(String(80), index=True)
    label: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    options: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

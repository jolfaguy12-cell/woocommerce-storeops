from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SystemSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: Any | None
    value_type: str
    group: str
    label: str
    description: str | None
    default_value: Any | None
    is_secret: bool
    is_public: bool
    is_editable: bool
    validation_rules: dict
    options: dict | list | None
    display_order: int
    updated_at: datetime


class SystemSettingUpdate(BaseModel):
    value: Any | None


class SettingsGroupRead(BaseModel):
    group: str
    label: str
    settings: list[SystemSettingRead]

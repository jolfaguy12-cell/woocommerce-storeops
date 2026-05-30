from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.settings.defaults import DEFAULT_SETTINGS
from app.modules.settings.models import SettingValueType, SystemSetting
from app.modules.users.models import User
from app.modules.users.service import record_audit

GROUP_LABELS = {
    "general": "General Settings",
    "wordpress_connector": "WordPress Connector Settings",
    "sync": "Sync Settings",
    "inventory": "Inventory Settings",
    "notifications": "Notification Settings",
    "reports": "Report Settings",
    "security": "Security Settings",
    "system": "System Settings",
}


def seed_system_settings(db: Session) -> None:
    for index, item in enumerate(DEFAULT_SETTINGS, start=1):
        setting = db.scalar(select(SystemSetting).where(SystemSetting.key == item["key"]))
        if setting is None:
            default_value = item.get("default_value")
            setting = SystemSetting(
                key=item["key"],
                value=default_value,
                value_type=item.get("value_type", SettingValueType.string.value),
                group=item["group"],
                label=item.get("label", item["key"].replace("_", " ").title()),
                description=item.get("description"),
                default_value=default_value,
                is_secret=item.get("is_secret", False),
                is_public=item.get("is_public", False),
                is_editable=item.get("is_editable", True),
                validation_rules=item.get("validation_rules", {}),
                options=item.get("options"),
                display_order=item.get("display_order", index),
            )
            db.add(setting)
    db.commit()


def _coerce_value(setting: SystemSetting, value: Any) -> Any:
    try:
        if setting.value_type == SettingValueType.integer.value:
            coerced = int(value)
        elif setting.value_type == SettingValueType.float.value:
            coerced = float(value)
        elif setting.value_type == SettingValueType.boolean.value:
            if isinstance(value, bool):
                coerced = value
            elif isinstance(value, str):
                coerced = value.strip().lower() in {"true", "1", "yes", "on"}
            else:
                coerced = bool(value)
        elif setting.value_type in {SettingValueType.json.value}:
            coerced = value
        else:
            coerced = "" if value is None else str(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid value for {setting.key}") from exc
    return coerced


def _validate_value(setting: SystemSetting, value: Any) -> None:
    rules = setting.validation_rules or {}
    options = setting.options
    if isinstance(options, list) and options and value not in options:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{setting.key} must be one of: {', '.join(map(str, options))}")
    if isinstance(value, (int, float)):
        if "min" in rules and value < rules["min"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{setting.key} must be at least {rules['min']}")
        if "max" in rules and value > rules["max"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{setting.key} must be at most {rules['max']}")
    if rules.get("format") == "HH:MM" and isinstance(value, str) and not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", value):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{setting.key} must use HH:MM time format")


def serialize_setting(setting: SystemSetting) -> dict:
    return {
        "id": setting.id,
        "key": setting.key,
        "value": "********" if setting.is_secret and setting.value else setting.value,
        "value_type": setting.value_type,
        "group": setting.group,
        "label": setting.label,
        "description": setting.description,
        "default_value": "********" if setting.is_secret and setting.default_value else setting.default_value,
        "is_secret": setting.is_secret,
        "is_public": setting.is_public,
        "is_editable": setting.is_editable,
        "validation_rules": setting.validation_rules or {},
        "options": setting.options,
        "display_order": setting.display_order,
        "updated_at": setting.updated_at,
    }


def list_settings(db: Session) -> list[SystemSetting]:
    seed_system_settings(db)
    return list(db.scalars(select(SystemSetting).order_by(SystemSetting.group, SystemSetting.display_order, SystemSetting.key)).all())


def get_setting_value(db: Session, key: str, default: Any = None) -> Any:
    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if setting is None:
        seed_system_settings(db)
        setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    return setting.value if setting is not None else default


def update_setting(db: Session, key: str, value: Any, actor: User) -> SystemSetting:
    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    if not setting.is_editable:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This setting is read-only")
    coerced = _coerce_value(setting, value)
    _validate_value(setting, coerced)
    old_value = "********" if setting.is_secret and setting.value else setting.value
    setting.value = coerced
    record_audit(
        db,
        "setting_changed",
        actor.id,
        "settings",
        "system_setting",
        setting.key,
        {"key": setting.key, "old_value": old_value, "new_value": "********" if setting.is_secret and coerced else coerced},
    )
    db.commit()
    db.refresh(setting)
    return setting

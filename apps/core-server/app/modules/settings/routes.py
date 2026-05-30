from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.settings.schemas import SettingsGroupRead, SystemSettingRead, SystemSettingUpdate
from app.modules.settings.service import GROUP_LABELS, list_settings, seed_system_settings, serialize_setting, update_setting
from app.modules.users.models import User

router = APIRouter()


@router.post("/seed", status_code=204)
def seed_settings(db: Session = Depends(get_db), current_user: User = Depends(require_permission("settings.manage"))) -> None:
    seed_system_settings(db)


@router.get("/", response_model=list[SettingsGroupRead])
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(require_permission("settings.view"))):
    grouped: dict[str, list] = {}
    for setting in list_settings(db):
        grouped.setdefault(setting.group, []).append(serialize_setting(setting))
    return [
        {"group": group, "label": GROUP_LABELS.get(group, group.replace("_", " ").title()), "settings": settings}
        for group, settings in grouped.items()
    ]


@router.patch("/{key}", response_model=SystemSettingRead)
def patch_setting(key: str, payload: SystemSettingUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("settings.manage"))):
    return serialize_setting(update_setting(db, key, payload.value, current_user))

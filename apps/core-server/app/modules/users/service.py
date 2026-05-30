from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users.models import AuditAction, AuditLog, BuiltInRole, User
from app.modules.users.schemas import UserCreate, UserUpdate


def record_audit(db: Session, action: AuditAction, actor_user_id: int | None = None, target_user_id: int | None = None, details: dict | None = None) -> None:
    db.add(AuditLog(action=action, actor_user_id=actor_user_id, target_user_id=target_user_id, details=details or {}))


def ensure_super_admin(actor: User | None) -> None:
    if actor is not None and actor.role != BuiltInRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin users can manage administrators by default")


def create_user(db: Session, payload: UserCreate, actor: User | None = None) -> User:
    ensure_super_admin(actor)
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        permissions=payload.permissions,
    )
    db.add(user)
    db.flush()
    record_audit(db, AuditAction.user_created, actor.id if actor else None, user.id, {"role": payload.role.value})
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate, actor: User | None = None) -> User:
    ensure_super_admin(actor)
    old_role = user.role
    old_permissions = set(user.permissions or [])
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.permissions is not None:
        user.permissions = payload.permissions
    if payload.is_active is not None:
        user.is_active = payload.is_active
    record_audit(db, AuditAction.user_updated, actor.id if actor else None, user.id)
    if payload.role is not None and payload.role != old_role:
        record_audit(db, AuditAction.role_changed, actor.id if actor else None, user.id, {"from": old_role.value, "to": payload.role.value})
    if payload.permissions is not None and set(payload.permissions) != old_permissions:
        record_audit(db, AuditAction.permissions_changed, actor.id if actor else None, user.id)
    db.commit()
    db.refresh(user)
    return user

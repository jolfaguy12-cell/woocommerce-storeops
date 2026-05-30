from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users.models import ALL_PERMISSIONS, AuditLog, BuiltInRole, Permission, ROLE_PERMISSION_DEFAULTS, Role, User
from app.modules.users.schemas import UserCreate, UserUpdate

ROLE_NAMES = {
    "super_admin": "Super Admin",
    "inventory_manager": "Inventory Manager",
    "sales_manager": "Sales Manager",
    "readonly_viewer": "Read-only Viewer",
    "accountant": "Accountant",
    "purchase_manager": "Purchase Manager",
    "supplier_manager": "Supplier Manager",
}


def record_audit(
    db: Session,
    action: str,
    user_id: int | None = None,
    module: str = "system",
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(AuditLog(
        action=action,
        user_id=user_id,
        module=module,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_json=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    ))


def ensure_super_admin(actor: User | None) -> None:
    if actor is not None and not (actor.is_superuser or actor.role == BuiltInRole.super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin users can manage users and roles by default")


def seed_roles_and_permissions(db: Session) -> None:
    permission_by_code: dict[str, Permission] = {}
    for code, (module, description) in ALL_PERMISSIONS.items():
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, module=module, description=description)
            db.add(permission)
            db.flush()
        permission_by_code[code] = permission

    for slug, permission_codes in ROLE_PERMISSION_DEFAULTS.items():
        role = db.scalar(select(Role).where(Role.slug == slug))
        if role is None:
            role = Role(name=ROLE_NAMES.get(slug, slug.replace("_", " ").title()), slug=slug, description=f"Built-in {ROLE_NAMES.get(slug, slug)} role", is_system_role=True)
            db.add(role)
            db.flush()
        role.permissions = [permission_by_code[code] for code in sorted(permission_codes) if code in permission_by_code]
    db.commit()


def super_admin_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.is_active == True, (User.is_superuser == True) | (User.role == BuiltInRole.super_admin))) or 0


def create_user(db: Session, payload: UserCreate, actor: User | None = None) -> User:
    ensure_super_admin(actor)
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    role_record = db.get(Role, payload.role_id) if payload.role_id else db.scalar(select(Role).where(Role.slug == payload.role.value))
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        role_id=role_record.id if role_record else None,
        permissions=payload.permissions,
        is_superuser=payload.role == BuiltInRole.super_admin,
        must_change_password=payload.must_change_password,
    )
    db.add(user)
    db.flush()
    record_audit(db, "user_created", actor.id if actor else None, "users", "user", user.id, {"role": payload.role.value})
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate, actor: User | None = None) -> User:
    ensure_super_admin(actor)
    if actor and actor.id == user.id and payload.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Users cannot deactivate themselves")
    old_role = user.role
    old_is_superuser = user.is_superuser
    if (payload.role is not None and user.role == BuiltInRole.super_admin and payload.role != BuiltInRole.super_admin) or (payload.is_active is False and user.role == BuiltInRole.super_admin):
        if super_admin_count(db) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove or downgrade the last Super Admin")
    if payload.email is not None:
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
        record_audit(db, "password_changed", actor.id if actor else None, "users", "user", user.id)
    if payload.role is not None:
        user.role = payload.role
        user.is_superuser = payload.role == BuiltInRole.super_admin
    if payload.role_id is not None:
        role_record = db.get(Role, payload.role_id)
        if role_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        user.role_id = role_record.id
    if payload.permissions is not None:
        user.permissions = payload.permissions
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.must_change_password is not None:
        user.must_change_password = payload.must_change_password
    record_audit(db, "user_updated", actor.id if actor else None, "users", "user", user.id)
    if payload.role is not None and payload.role != old_role:
        record_audit(db, "role_changed", actor.id if actor else None, "users", "user", user.id, {"from": old_role.value, "to": payload.role.value})
    if old_is_superuser != user.is_superuser:
        record_audit(db, "role_changed", actor.id if actor else None, "users", "user", user.id, {"is_superuser": user.is_superuser})
    db.commit()
    db.refresh(user)
    return user

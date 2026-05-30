from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.users.models import ALL_PERMISSIONS, Permission, Role, User
from app.modules.users.schemas import PermissionRead, RoleRead, UserCreate, UserRead, UserUpdate
from app.modules.users.service import create_user, record_audit, seed_roles_and_permissions, super_admin_count, update_user

router = APIRouter()


@router.post("/bootstrap-roles", status_code=status.HTTP_204_NO_CONTENT)
def bootstrap_roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.manage"))) -> None:
    seed_roles_and_permissions(db)


@router.get("/roles", response_model=list[RoleRead])
def roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.view"))):
    seed_roles_and_permissions(db)
    return db.scalars(select(Role).order_by(Role.name)).unique().all()


@router.get("/permissions", response_model=list[PermissionRead])
def permissions(db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.view"))):
    seed_roles_and_permissions(db)
    return db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.view"))):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.create"))):
    seed_roles_and_permissions(db)
    return create_user(db, payload, actor=current_user)


@router.patch("/{user_id}", response_model=UserRead)
def edit_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.update"))):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return update_user(db, user, payload, actor=current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.delete"))) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Users cannot delete themselves")
    if user.is_superuser and super_admin_count(db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last Super Admin")
    db.delete(user)
    record_audit(db, "user_deleted", current_user.id, "users", "user", user.id)
    db.commit()


@router.post("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.delete"))) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_user(db, user, UserUpdate(is_active=False), actor=current_user)

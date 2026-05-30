from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.users.models import AuditAction, DEFAULT_ROLE_PERMISSIONS, User
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate
from app.modules.users.service import create_user, record_audit, update_user

router = APIRouter()


@router.get("/roles")
def roles(current_user: User = Depends(require_permission("users.view"))) -> dict[str, list[str]]:
    return {role.value: sorted(permissions) for role, permissions in DEFAULT_ROLE_PERMISSIONS.items()}


@router.get("/permissions")
def permissions(current_user: User = Depends(require_permission("users.view"))) -> list[str]:
    values: set[str] = set()
    for permissions_for_role in DEFAULT_ROLE_PERMISSIONS.values():
        values.update(permissions_for_role)
    return sorted(values)


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.view"))):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.create"))):
    return create_user(db, payload, actor=current_user)


@router.patch("/{user_id}", response_model=UserRead)
def edit_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.update"))):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return update_user(db, user, payload, actor=current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.delete"))) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    record_audit(db, AuditAction.user_deactivated, actor_user_id=current_user.id, target_user_id=user.id)
    db.commit()

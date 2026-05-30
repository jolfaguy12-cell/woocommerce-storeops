from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.modules.users.models import AuditAction, User
from app.modules.users.service import record_audit

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    if not payload.username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        record_audit(db, AuditAction.login_failed, details={"username": payload.username},)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    record_audit(db, AuditAction.login_success, actor_user_id=user.id, target_user_id=user.id, details={"ip": request.client.host if request.client else None})
    db.commit()
    return {
        "access_token": create_access_token(user.username, {"role": user.role.value, "permissions": sorted(user.effective_permissions())}),
        "token_type": "bearer",
    }

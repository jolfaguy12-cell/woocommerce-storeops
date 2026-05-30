from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import UserRead
from app.modules.users.service import record_audit

router = APIRouter()

FAILED_LOGIN_ATTEMPTS: dict[str, list[datetime]] = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW = timedelta(minutes=10)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _check_lockout(username: str) -> None:
    now = datetime.now(timezone.utc)
    FAILED_LOGIN_ATTEMPTS[username] = [ts for ts in FAILED_LOGIN_ATTEMPTS[username] if now - ts <= LOCKOUT_WINDOW]
    if len(FAILED_LOGIN_ATTEMPTS[username]) >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts. Try again later.")


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    if not payload.username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")
    _check_lockout(payload.username)
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        FAILED_LOGIN_ATTEMPTS[payload.username].append(datetime.now(timezone.utc))
        record_audit(db, "login_failure", module="auth", metadata={"username": payload.username}, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    FAILED_LOGIN_ATTEMPTS.pop(payload.username, None)
    user.last_login_at = datetime.now(timezone.utc)
    record_audit(db, "login_success", user.id, "auth", "user", user.id, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
    db.commit()
    access_token = create_access_token(user.username, {"role": user.role.value, "permissions": sorted(user.effective_permissions())})
    settings = get_settings()
    response.set_cookie("storeops_access_token", access_token, httponly=True, secure=settings.environment == "production", samesite="lax", max_age=3600)
    return {"access_token": access_token, "token_type": "bearer", "must_change_password": user.must_change_password}


@router.post("/logout")
def logout(request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    record_audit(db, "logout", current_user.id, "auth", "user", current_user.id, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
    db.commit()
    response.delete_cookie("storeops_access_token")
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.password_hash):
        record_audit(db, "password_change_failed", current_user.id, "auth", "user", current_user.id, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    current_user.must_change_password = False
    record_audit(db, "password_changed", current_user.id, "auth", "user", current_user.id, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
    db.commit()
    return {"status": "ok"}

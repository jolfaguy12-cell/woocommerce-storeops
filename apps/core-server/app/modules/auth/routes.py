from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    # Phase 1 skeleton: wire to User model and password verification during bootstrap implementation.
    if not payload.username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")
    return {"access_token": create_access_token(payload.username, {"role": "super_admin"}), "token_type": "bearer"}

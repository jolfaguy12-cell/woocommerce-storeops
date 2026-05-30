from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import time
from typing import Any
from fastapi import Header, HTTPException, Request, status
from jose import jwt
from passlib.context import CryptContext

from app.config.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires}
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


async def verify_wordpress_signature(
    request: Request,
    x_storeops_api_key: str = Header(...),
    x_storeops_timestamp: str = Header(...),
    x_storeops_signature: str = Header(...),
) -> None:
    settings = get_settings()
    if settings.reject_insecure_http and request.url.scheme != "https":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTPS is required in production")
    if not hmac.compare_digest(x_storeops_api_key, settings.wordpress_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    try:
        timestamp = int(x_storeops_timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp") from exc
    if abs(int(time.time()) - timestamp) > settings.hmac_timestamp_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Request timestamp outside tolerance")
    body = await request.body()
    expected = hmac.new(settings.wordpress_hmac_secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_storeops_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

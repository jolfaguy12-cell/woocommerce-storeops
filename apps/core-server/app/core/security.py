from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets
import time
from typing import Any
from fastapi import Header, HTTPException, Request, status
from jose import jwt

from app.config.settings import get_settings

ALGORITHM = "HS256"
PASSWORD_HASH_SCHEME = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 390_000
PASSWORD_SALT_BYTES = 24


def _encode_digest(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_digest(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def hash_password(password: str) -> str:
    """Hash an admin password without bcrypt's 72-byte input limit."""
    if not password:
        raise ValueError("Password must not be empty")
    salt = secrets.token_urlsafe(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_HASH_ITERATIONS)
    return f"{PASSWORD_HASH_SCHEME}${PASSWORD_HASH_ITERATIONS}${salt}${_encode_digest(digest)}"


def _verify_pbkdf2_password(password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations, salt, expected_digest = hashed_password.split("$", 3)
        if scheme != PASSWORD_HASH_SCHEME:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
        return hmac.compare_digest(digest, _decode_digest(expected_digest))
    except (TypeError, ValueError, OverflowError):
        return False


def _verify_legacy_bcrypt_password(password: str, hashed_password: str) -> bool:
    """Best-effort compatibility for old bcrypt hashes; new hashes use PBKDF2."""
    if not hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        return False
    try:
        from passlib.context import CryptContext  # type: ignore

        return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(password, hashed_password)
    except Exception:
        return False


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    if hashed_password.startswith(f"{PASSWORD_HASH_SCHEME}$"):
        return _verify_pbkdf2_password(password, hashed_password)
    return _verify_legacy_bcrypt_password(password, hashed_password)


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

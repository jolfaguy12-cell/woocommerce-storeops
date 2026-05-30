#!/usr/bin/env python3
"""Check StoreOps database connectivity with human-readable diagnostics.

Run from the repository root before Alembic migrations:
    python3 scripts/check_db.py
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import socket
import sys
from urllib.parse import parse_qsl, quote, unquote, urlsplit, urlunsplit

LOG_PATH = Path("apps/core-server/app/logs/db-check.log")
def configure_logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("storeops.db_check")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def load_env_file() -> dict[str, str]:
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(".env.example")
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def database_url() -> tuple[str | None, str]:
    env_values = load_env_file()
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"], "environment"
    if env_values.get("DATABASE_URL"):
        return env_values["DATABASE_URL"], ".env/.env.example"
    return None, "missing"


def mask_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        credentials, host = netloc.rsplit("@", 1)
        username = unquote(credentials.split(":", 1)[0]) if credentials else ""
        netloc = f"{quote(username)}:***@{host}" if username else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def parsed_host_port(url: str) -> tuple[str | None, int]:
    parts = urlsplit(url)
    return parts.hostname, parts.port or 5432


def likely_fix(host: str | None) -> str:
    if host in {"postgres", "db", "database"}:
        return (
            "The database host looks like a Docker Compose service name. Use this host only inside Docker Compose. "
            "If you are running Alembic directly on the server, use 127.0.0.1 or localhost in DATABASE_URL."
        )
    if host in {"127.0.0.1", "localhost"}:
        return "Verify PostgreSQL is installed, running locally, listening on port 5432, and the storeops database/user exist."
    return "Verify the DATABASE_URL host, DNS, firewall, PostgreSQL service, and Docker Compose network if applicable."


def psycopg_connect_kwargs(url: str) -> dict[str, str | int]:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    return {
        "host": parts.hostname or "",
        "port": parts.port or 5432,
        "dbname": parts.path.lstrip("/"),
        "user": unquote(parts.username or ""),
        "password": unquote(parts.password or ""),
        "connect_timeout": int(query.get("connect_timeout", "5")),
    }


def main() -> int:
    logger = configure_logger()
    url, source = database_url()
    print("WooCommerce StoreOps database connectivity check")
    print("------------------------------------------------")

    if not url:
        message = "DATABASE_URL is not set. Copy .env.example to .env and configure DATABASE_URL before migrations."
        print(f"❌ {message}")
        logger.error(message)
        return 2

    safe_url = mask_url(url)
    host, port = parsed_host_port(url)
    print(f"DATABASE_URL loaded from: {source}")
    print(f"Database URL: {safe_url}")
    print(f"Database host: {host or 'not found'}")
    print(f"Database port: {port}")
    logger.info("Checking database connectivity for %s", safe_url)

    if not host:
        message = "DATABASE_URL does not include a database host."
        print(f"❌ {message}")
        print(f"Likely fix: {likely_fix(host)}")
        logger.error(message)
        return 2

    try:
        socket.getaddrinfo(host, port)
    except socket.gaierror as exc:
        message = f"Database host '{host}' could not be resolved: {exc}."
        print(f"❌ {message}")
        print(f"Likely fix: {likely_fix(host)}")
        logger.error("Database host could not be resolved: host=%s error=%s", host, exc)
        return 1

    print("✅ Database host resolved successfully.")

    try:
        import psycopg
    except ModuleNotFoundError:
        message = "psycopg is not installed, so the script could not open a database connection."
        print(f"⚠️ {message}")
        print("Install Core Server dependencies first: python3 -m pip install -r apps/core-server/requirements.txt")
        logger.warning(message)
        return 3

    try:
        with psycopg.connect(**psycopg_connect_kwargs(url)) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 - diagnostics script should catch connection failures broadly.
        print(f"❌ Database connection failed: {exc.__class__.__name__}: {exc}")
        print(f"Likely fix: {likely_fix(host)}")
        print("Also verify the database name, user, password, and local/Docker port mapping.")
        logger.error("Database connection failed for %s: %s: %s", safe_url, exc.__class__.__name__, exc)
        return 1

    print("✅ Database connection succeeded. You can run: cd apps/core-server && alembic upgrade head")
    logger.info("Database connection succeeded for %s", safe_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())

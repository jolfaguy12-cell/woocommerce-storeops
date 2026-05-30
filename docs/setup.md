# Installation Guide

1. Copy `.env.example` to `.env` and replace secrets.
2. Run `docker compose build`.
3. Run `docker compose up -d postgres redis`.
4. Run `docker compose run --rm core-server alembic upgrade head`.
5. Run `docker compose up -d`.
6. Install and configure the WordPress connector plugin.


## Database host selection

Use `postgres` in `DATABASE_URL` only when the Core Server runs inside Docker Compose. Use `127.0.0.1` or `localhost` when running FastAPI or Alembic directly on the host. Before migrations, run `python3 scripts/check_db.py` from the repository root for a human-readable connectivity check.


## Port safety

Default local binding is `APP_HOST=127.0.0.1` and `APP_PORT=8088`. Run `ss -tulpn` before changing ports. PostgreSQL and Redis should remain on the Docker network only and should not be publicly exposed.

# Installation Guide

1. Copy `.env.example` to `.env` and replace secrets.
2. Run `docker compose build core-server` to build the shared Core Server image used by the API, Celery worker, and Celery Beat.
3. Run `docker compose up -d postgres redis`.
4. Run `docker compose run --rm core-server alembic upgrade head`.
5. Run `docker compose up -d core-server celery-worker celery-beat`.
6. Install and configure the WordPress connector plugin.


## Docker build snapshot errors

If Docker fails during image export with `failed to prepare extraction snapshot` or `parent snapshot ... does not exist`, rebuild the single shared Core Server image instead of repeatedly exporting duplicate API/worker/beat images:

```bash
docker compose build --no-cache core-server
docker compose up -d core-server celery-worker celery-beat
```

The Compose file intentionally gives `celery-worker` and `celery-beat` the same image as `core-server`; only `core-server` has a `build:` section. If the host Docker builder cache is already corrupted, run `docker builder prune` only when no important builds are running.

## Database host selection

Use `postgres` in `DATABASE_URL` only when the Core Server runs inside Docker Compose. Use `127.0.0.1` or `localhost` when running FastAPI or Alembic directly on the host. Before migrations, run `python3 scripts/check_db.py` from the repository root for a human-readable connectivity check.


## Port safety

Default local binding is `APP_HOST=127.0.0.1` and `APP_PORT=8088`. Run `ss -tulpn` before changing ports. PostgreSQL and Redis should remain on the Docker network only and should not be publicly exposed.

## First Super Admin

Set these variables in `.env` before creating the first dashboard user:

```env
STOREOPS_ADMIN_USERNAME=admin
STOREOPS_ADMIN_EMAIL=admin@example.com
STOREOPS_ADMIN_PASSWORD=change-this-admin-password
```

After migrations, run:

```bash
docker compose exec core-server python3 -m app.cli.create_admin
```

The admin password is hashed with PBKDF2-SHA256 and is never printed. If an older build reported a passlib/bcrypt `password cannot be longer than 72 bytes` error, pull this update, rebuild the Core Server image, and run the bootstrap command again.

If running on the host from the repository root, run:

```bash
python3 scripts/create_admin.py
```

The command refuses to create another bootstrap admin if any users already exist and never prints the password.

## Sync Center

The Sync Center is protected by permissions. Users with `sync.view` can see sync history, `sync.run_full` can start full product sync, and `sync.run_changed` can start changed-product sync.

# Core Server

Python 3.11 or newer FastAPI service responsible for heavy StoreOps work: inventory analysis, sync processing, authentication, Telegram, reports, logs, and future modules.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Workers

```bash
celery -A app.jobs.celery_app worker -l info
celery -A app.jobs.celery_app beat -l info
```

## Database preflight

From the repository root, run:

```bash
python3 scripts/check_db.py
```

Use `postgres` as the database host inside Docker Compose and `127.0.0.1` or `localhost` when running Alembic directly on the host.

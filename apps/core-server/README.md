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
celery -A app.jobs.celery_app.celery_app worker --loglevel=info
celery -A app.jobs.celery_app.celery_app beat --loglevel=info
```

Verify registered tasks:

```bash
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app inspect registered
docker compose logs celery-worker --tail=100
docker compose logs celery-beat --tail=100
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app call app.jobs.debug_tasks.celery_ping
```

If `inspect registered` returns `- empty -`, the worker is running but task modules were not imported into the Celery app. Check `celery_app.conf.imports`, explicit task-module imports, and the Docker Compose `-A app.jobs.celery_app.celery_app` app path. If old unregistered task messages remain after a deployment, restart worker/beat first. Purge the queue only when no important jobs are pending:

```bash
docker compose up -d --build core-server celery-worker celery-beat
docker compose restart celery-worker celery-beat
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app purge
```

## Database preflight

From the repository root, run:

```bash
python3 scripts/check_db.py
```

Use `postgres` as the database host inside Docker Compose and `127.0.0.1` or `localhost` when running Alembic directly on the host.

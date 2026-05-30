# Core Server

FastAPI service responsible for heavy StoreOps work: inventory analysis, sync processing, authentication, Telegram, reports, logs, and future modules.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Workers

```bash
celery -A app.jobs.celery_app worker -l info
celery -A app.jobs.celery_app beat -l info
```

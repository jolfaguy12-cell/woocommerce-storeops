from celery import Celery

from app.config.settings import get_settings

settings = get_settings()
celery_app = Celery("storeops", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.beat_schedule = {
    "inventory-fast-scan-every-minute": {
        "task": "app.jobs.inventory_tasks.fast_inventory_scan",
        "schedule": settings.inventory_fast_scan_interval_seconds,
    },
}
celery_app.conf.timezone = "UTC"

import logging
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from celery import Celery
from celery.signals import after_setup_logger, beat_init, worker_ready

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TASK_MODULES = (
    "app.jobs.inventory_tasks",
    "app.jobs.debug",
)

celery_app = Celery(
    "storeops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=list(TASK_MODULES),
)

# Expose a conventional `app` symbol so `celery -A app.jobs.celery_app worker`
# and tools that look for `app`/`celery` both resolve the same Celery instance.
app = celery_app

celery_app.conf.imports = TASK_MODULES
celery_app.conf.beat_schedule = {
    "inventory-fast-scan-every-minute": {
        "task": "app.jobs.inventory_tasks.fast_inventory_scan",
        "schedule": settings.inventory_fast_scan_interval_seconds,
    },
}
celery_app.conf.timezone = "UTC"


def mask_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        credentials, host = netloc.rsplit("@", 1)
        username = unquote(credentials.split(":", 1)[0]) if credentials else ""
        netloc = f"{quote(username)}:***@{host}" if username else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def log_celery_configuration(active_logger: logging.Logger) -> None:
    registered_tasks = sorted(
        name for name in celery_app.tasks.keys()
        if name.startswith("app.jobs.")
    )
    active_logger.info("StoreOps Celery app path: app.jobs.celery_app:celery_app")
    active_logger.info("StoreOps Celery broker: %s", mask_url(settings.celery_broker_url))
    active_logger.info("StoreOps Celery loaded task modules: %s", ", ".join(TASK_MODULES))
    active_logger.info("StoreOps Celery registered StoreOps tasks: %s", ", ".join(registered_tasks) or "none yet")
    active_logger.info("StoreOps Celery beat schedule entries: %s", ", ".join(sorted(celery_app.conf.beat_schedule.keys())))


@after_setup_logger.connect
def on_after_setup_logger(logger: logging.Logger, *args, **kwargs) -> None:
    log_celery_configuration(logger)


@worker_ready.connect
def on_worker_ready(sender=None, **kwargs) -> None:
    active_logger = logging.getLogger(__name__)
    active_logger.info("StoreOps Celery worker is ready")
    log_celery_configuration(active_logger)


@beat_init.connect
def on_beat_init(sender=None, **kwargs) -> None:
    active_logger = logging.getLogger(__name__)
    active_logger.info("StoreOps Celery beat started")
    log_celery_configuration(active_logger)

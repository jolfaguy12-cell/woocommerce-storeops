import importlib
import logging
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from celery import Celery
from celery.signals import after_setup_logger, beat_init, worker_ready

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TASK_MODULES = (
    "app.jobs.inventory_tasks",
    "app.jobs.debug_tasks",
)

celery_app = Celery(
    "storeops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Compatibility alias. Docker Compose intentionally uses the explicit variable
# path: app.jobs.celery_app.celery_app
app = celery_app

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    imports=TASK_MODULES,
)

celery_app.conf.beat_schedule = {
    "inventory-fast-scan-every-minute": {
        "task": "app.jobs.inventory_tasks.fast_inventory_scan",
        "schedule": 60.0,
    },
}


def import_task_modules() -> None:
    """Import task modules explicitly so workers always register StoreOps tasks."""
    for task_module in TASK_MODULES:
        importlib.import_module(task_module)


# Import task modules at module import time. This is deliberate: `celery inspect
# registered` must not depend on some other module importing tasks first.
import_task_modules()


def mask_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        credentials, host = netloc.rsplit("@", 1)
        username = unquote(credentials.split(":", 1)[0]) if credentials else ""
        netloc = f"{quote(username)}:***@{host}" if username else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def registered_storeops_tasks() -> list[str]:
    return sorted(name for name in celery_app.tasks.keys() if name.startswith("app.jobs."))


def log_celery_configuration(active_logger: logging.Logger) -> None:
    # Import again in worker/beat processes in case a loader reset occurred before
    # process boot. Re-importing modules is idempotent in Python.
    import_task_modules()
    active_logger.info("StoreOps Celery app path: app.jobs.celery_app.celery_app")
    active_logger.info("StoreOps Celery broker: %s", mask_url(settings.celery_broker_url))
    active_logger.info("StoreOps Celery imports: %s", list(celery_app.conf.imports or ()))
    active_logger.info("StoreOps Celery loaded task modules: %s", ", ".join(TASK_MODULES))
    active_logger.info("StoreOps Celery registered StoreOps tasks: %s", ", ".join(registered_storeops_tasks()) or "none")
    active_logger.info("StoreOps Celery all task keys: %s", ", ".join(sorted(celery_app.tasks.keys())))
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

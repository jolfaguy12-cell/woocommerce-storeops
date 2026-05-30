import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.jobs.inventory_tasks.fast_inventory_scan")
def fast_inventory_scan() -> dict[str, str]:
    logger.info("fast_inventory_scan_started")
    return {"status": "queued"}


@celery_app.task(name="app.jobs.inventory_tasks.full_inventory_scan")
def full_inventory_scan() -> dict[str, str]:
    logger.info("full_inventory_scan_started")
    return {"status": "queued"}


@celery_app.task(name="app.jobs.inventory_tasks.changed_products_sync")
def changed_products_sync() -> dict[str, str]:
    logger.info("changed_products_sync_started")
    return {"status": "queued"}


@celery_app.task(name="app.jobs.inventory_tasks.health_check_task")
def health_check_task() -> dict[str, str]:
    logger.info("celery_health_check_task_started")
    return {"status": "ok"}

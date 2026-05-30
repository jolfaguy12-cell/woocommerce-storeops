import logging
from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def fast_inventory_scan() -> dict[str, str]:
    logger.info("fast_inventory_scan_started")
    return {"status": "queued"}


@celery_app.task
def full_inventory_scan() -> dict[str, str]:
    logger.info("full_inventory_scan_started")
    return {"status": "queued"}

import logging

from app.db.session import SessionLocal
from app.jobs.celery_app import celery_app
from app.modules.sync.models import SyncJobType, SyncTrigger
from app.modules.sync.service import create_sync_job, run_full_product_sync
from app.modules.users.service import record_audit

logger = logging.getLogger(__name__)


@celery_app.task(name="app.jobs.inventory_tasks.fast_inventory_scan")
def fast_inventory_scan() -> dict[str, str]:
    logger.info("fast_inventory_scan_started")
    return {"status": "ok", "task": "fast_inventory_scan"}


@celery_app.task(name="app.jobs.inventory_tasks.full_inventory_scan")
def full_inventory_scan(job_id: int | None = None) -> dict:
    logger.info("full_inventory_scan_started job_id=%s", job_id)
    with SessionLocal() as db:
        if job_id is None:
            job = create_sync_job(db, SyncJobType.full_product_sync.value, SyncTrigger.scheduled.value, metadata={"per_page": 50})
            job_id = job.id
        return run_full_product_sync(db, job_id)


@celery_app.task(name="app.jobs.inventory_tasks.changed_products_sync")
def changed_products_sync(job_id: int | None = None) -> dict[str, str | int | None]:
    logger.info("changed_products_sync_started job_id=%s", job_id)
    with SessionLocal() as db:
        if job_id is None:
            job = create_sync_job(db, SyncJobType.changed_products_sync.value, SyncTrigger.scheduled.value)
            job_id = job.id
        record_audit(db, "changed_sync_triggered", module="sync", entity_type="sync_job", entity_id=job_id)
        db.commit()
    return {"status": "queued", "task": "changed_products_sync", "job_id": job_id}


@celery_app.task(name="app.jobs.inventory_tasks.health_check_task")
def health_check_task() -> dict[str, str]:
    logger.info("celery_health_check_task_started")
    return {"status": "ok", "task": "health_check_task"}

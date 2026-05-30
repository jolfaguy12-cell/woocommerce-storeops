from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.jobs.inventory_tasks import changed_products_sync, full_inventory_scan
from app.modules.auth.dependencies import require_permission
from app.modules.sync.models import SyncJob, SyncJobStatus, SyncJobType, SyncTrigger
from app.modules.sync.schemas import SyncJobRead, SyncTriggerResponse
from app.modules.sync.service import create_sync_job, running_full_sync
from app.modules.users.models import User
from app.modules.users.service import record_audit

router = APIRouter()


@router.get("/status")
def status_view(db: Session = Depends(get_db), current_user: User = Depends(require_permission("sync.view"))):
    current = db.scalar(select(SyncJob).where(SyncJob.status.in_([SyncJobStatus.pending.value, SyncJobStatus.running.value])).order_by(SyncJob.created_at.desc()))
    last_full_success = db.scalar(select(SyncJob).where(SyncJob.job_type == SyncJobType.full_product_sync.value, SyncJob.status == SyncJobStatus.completed.value).order_by(SyncJob.finished_at.desc()))
    last_full_failed = db.scalar(select(SyncJob).where(SyncJob.job_type == SyncJobType.full_product_sync.value, SyncJob.status == SyncJobStatus.failed.value).order_by(SyncJob.finished_at.desc()))
    last_changed = db.scalar(select(SyncJob).where(SyncJob.job_type == SyncJobType.changed_products_sync.value).order_by(SyncJob.created_at.desc()))
    return {
        "current_job": current.id if current else None,
        "current_status": current.status if current else "idle",
        "last_successful_full_sync": last_full_success.finished_at if last_full_success else None,
        "last_failed_full_sync": last_full_failed.finished_at if last_full_failed else None,
        "last_changed_products_sync": last_changed.finished_at if last_changed else None,
    }


@router.get("/jobs", response_model=list[SyncJobRead])
def jobs(db: Session = Depends(get_db), current_user: User = Depends(require_permission("sync.view"))):
    return db.scalars(select(SyncJob).order_by(SyncJob.created_at.desc()).limit(100)).all()


@router.get("/jobs/{job_id}", response_model=SyncJobRead)
def job_detail(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sync.view"))):
    job = db.get(SyncJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync job not found")
    return job


@router.post("/full-products", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_full_products(db: Session = Depends(get_db), current_user: User = Depends(require_permission("sync.run_full"))):
    existing = running_full_sync(db)
    if existing:
        return SyncTriggerResponse(job_id=existing.id, status=existing.status, message="Full product sync is already running or pending")
    job = create_sync_job(db, SyncJobType.full_product_sync.value, SyncTrigger.manual.value, current_user.id, {"per_page": 50})
    record_audit(db, "full_sync_triggered", current_user.id, "sync", "sync_job", job.id)
    db.commit()
    task = full_inventory_scan.delay(job.id)
    return SyncTriggerResponse(job_id=job.id, celery_task_id=task.id, status=job.status, message="Full product sync queued")


@router.post("/changed-products", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_changed_products(db: Session = Depends(get_db), current_user: User = Depends(require_permission("sync.run_changed"))):
    job = create_sync_job(db, SyncJobType.changed_products_sync.value, SyncTrigger.manual.value, current_user.id)
    record_audit(db, "changed_sync_triggered", current_user.id, "sync", "sync_job", job.id)
    db.commit()
    task = changed_products_sync.delay(job.id)
    return SyncTriggerResponse(job_id=job.id, celery_task_id=task.id, status=job.status, message="Changed-products sync queued")


@router.post("/check-wordpress")
def check_wordpress(current_user: User = Depends(require_permission("sync.view"))):
    return {"status": "queued", "message": "WordPress connection check endpoint is ready for Sync Center integration"}

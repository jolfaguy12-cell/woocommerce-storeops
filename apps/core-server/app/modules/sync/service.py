import hashlib
import hmac
import json
import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.datetime_utils import utc_now
from app.modules.inventory.schemas import ProductSyncPayload
from app.modules.inventory.upsert import upsert_products
from app.modules.settings.service import get_setting_value
from app.modules.sync.models import SyncJob, SyncJobStatus, SyncJobType
from app.modules.users.service import record_audit

logger = logging.getLogger(__name__)


def running_full_sync(db: Session) -> SyncJob | None:
    return db.scalar(select(SyncJob).where(SyncJob.job_type == SyncJobType.full_product_sync.value, SyncJob.status.in_([SyncJobStatus.pending.value, SyncJobStatus.running.value])).order_by(SyncJob.created_at.desc()))


def create_sync_job(db: Session, job_type: str, triggered_by: str, user_id: int | None = None, metadata: dict | None = None) -> SyncJob:
    job = SyncJob(job_type=job_type, status=SyncJobStatus.pending.value, triggered_by=triggered_by, triggered_by_user_id=user_id, metadata_json=metadata or {})
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def mark_job(db: Session, job: SyncJob, status: str, error_message: str | None = None) -> None:
    if status == SyncJobStatus.running.value:
        job.started_at = utc_now()
    if status in {SyncJobStatus.completed.value, SyncJobStatus.failed.value, SyncJobStatus.cancelled.value}:
        job.finished_at = utc_now()
    job.status = status
    if error_message:
        job.error_message = error_message[:4000]
    db.commit()


def _signed_headers(route: str, query: dict[str, object] | None = None) -> dict[str, str]:
    settings = get_settings()
    headers = {"x-storeops-api-key": settings.wordpress_api_key, "Accept": "application/json"}
    if settings.wordpress_hmac_secret:
        timestamp = str(int(time.time()))
        query_json = json.dumps({key: str(value) for key, value in (query or {}).items()}, separators=(",", ":"))
        message = f"{timestamp}.GET.{route}?{query_json}"
        signature = hmac.new(settings.wordpress_hmac_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        headers.update({"x-storeops-timestamp": timestamp, "x-storeops-signature": signature})
    return headers


def _connector_url(path: str) -> str:
    settings = get_settings()
    base = settings.wordpress_connector_url.rstrip("/")
    if not base:
        raise RuntimeError("WORDPRESS_CONNECTOR_URL is not configured")
    return f"{base}/{path.lstrip('/')}"


def fetch_wordpress_page(page: int, per_page: int = 50, timeout_seconds: int = 20, retry_count: int = 3, retry_delay_seconds: int = 2) -> dict:
    route = "/storeops/v1/products"
    query = {"page": page, "per_page": per_page, "status": "any"}
    url = _connector_url("products")
    for attempt in range(1, retry_count + 1):
        try:
            with httpx.Client(timeout=float(timeout_seconds)) as client:
                response = client.get(url, params=query, headers=_signed_headers(route, query))
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("wordpress_page_fetch_failed page=%s attempt=%s error=%s", page, attempt, exc)
            if attempt >= retry_count:
                raise
            time.sleep(max(retry_delay_seconds, 0) * (2 ** (attempt - 1)))
    raise RuntimeError("unreachable")


def run_full_product_sync(db: Session, job_id: int) -> dict[str, int | str]:
    job = db.get(SyncJob, job_id)
    if job is None:
        raise RuntimeError(f"Sync job {job_id} not found")
    mark_job(db, job, SyncJobStatus.running.value)
    page = 1
    per_page = int(job.metadata_json.get("per_page", get_setting_value(db, "full_sync_batch_size", 50))) if job.metadata_json else int(get_setting_value(db, "full_sync_batch_size", 50))
    timeout_seconds = int(get_setting_value(db, "sync_request_timeout_seconds", 20))
    retry_count = int(get_setting_value(db, "sync_retry_count", 3))
    retry_delay_seconds = int(get_setting_value(db, "sync_retry_delay_seconds", 2))
    try:
        while True:
            result = fetch_wordpress_page(page, per_page, timeout_seconds, retry_count, retry_delay_seconds)
            items = result.get("items", [])
            payload = [ProductSyncPayload(**item) for item in items]
            stats = upsert_products(payload, db) if payload else {"processed_items": 0, "created_items": 0, "updated_items": 0, "failed_items": 0}
            db.refresh(job)
            job.total_items = int(result.get("total", job.total_items or 0))
            job.processed_items += stats["processed_items"]
            job.created_items += stats["created_items"]
            job.updated_items += stats["updated_items"]
            job.failed_items += stats["failed_items"]
            db.commit()
            logger.info("full_product_sync_page_completed job_id=%s page=%s processed=%s", job.id, page, stats["processed_items"])
            if not result.get("has_more"):
                break
            page += 1
        mark_job(db, job, SyncJobStatus.completed.value)
        record_audit(db, "sync_completed", job.triggered_by_user_id, "sync", "sync_job", job.id, {"job_type": job.job_type, "processed_items": job.processed_items})
        db.commit()
        return {"status": job.status, "processed_items": job.processed_items, "created_items": job.created_items, "updated_items": job.updated_items, "failed_items": job.failed_items}
    except Exception as exc:
        db.rollback()
        job = db.get(SyncJob, job_id)
        if job:
            job.failed_items += 1
            mark_job(db, job, SyncJobStatus.failed.value, str(exc))
            record_audit(db, "sync_failed", job.triggered_by_user_id, "sync", "sync_job", job.id, {"error": str(exc)})
            db.commit()
        logger.exception("full_product_sync_failed job_id=%s", job_id)
        return {"status": SyncJobStatus.failed.value, "error": str(exc)}


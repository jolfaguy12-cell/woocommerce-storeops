from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SyncJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    total_items: int
    processed_items: int
    created_items: int
    updated_items: int
    failed_items: int
    error_message: str | None
    triggered_by: str
    triggered_by_user_id: int | None
    metadata_json: dict
    created_at: datetime


class SyncTriggerResponse(BaseModel):
    job_id: int
    celery_task_id: str | None = None
    status: str
    message: str

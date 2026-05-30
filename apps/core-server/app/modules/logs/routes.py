from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.users.models import AuditLog, User

router = APIRouter()


@router.get("/audit")
def audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("logs.view")),
):
    rows = db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "module": row.module,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "metadata": row.metadata_json,
            "created_at": row.created_at,
        }
        for row in rows
    ]

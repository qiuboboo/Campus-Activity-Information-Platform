import json

from flask import current_app

from ..extensions import db
from ..models import AuditLog


def create_audit_log(
    actor_id: int,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    summary: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
    )
    db.session.add(log)
    db.session.flush()
    return log

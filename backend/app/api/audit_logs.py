from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..models import AuditLog
from ..utils.auth import roles_required

audit_logs_bp = Blueprint("audit_logs", __name__)


def _audit_log_payload(log: AuditLog) -> dict:
    data = log.to_dict()
    actor_name = log.actor.username if log.actor else f"用户 #{log.actor_id}"
    target = data.get("target_type") or "system"
    if data.get("target_id") is not None:
        target = f"{target} #{data['target_id']}"
    data.update({
        "actor": actor_name,
        "target": target,
    })
    return data


@audit_logs_bp.get("")
@roles_required("admin")
def list_audit_logs():
    actor_id = request.args.get("actor_id", type=int)
    action = (request.args.get("action") or "").strip()
    target_type = (request.args.get("target_type") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)

    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if actor_id is not None:
        query = query.filter_by(actor_id=actor_id)
    if action:
        query = query.filter_by(action=action)
    if target_type:
        query = query.filter_by(target_type=target_type)

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [_audit_log_payload(log) for log in items.items],
        "page": page,
        "per_page": per_page,
        "total": items.total,
    })

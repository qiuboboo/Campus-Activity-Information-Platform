from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..celery_app import celery

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks/<task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id: str):
    result = celery.AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "state": result.state,
    }
    if result.state == "PENDING":
        payload["result"] = None
        payload["error"] = None
    elif result.state == "FAILURE":
        payload["result"] = None
        info = result.info
        if isinstance(info, Exception):
            payload["error"] = str(info)
        elif isinstance(info, dict):
            payload["error"] = info.get("error", str(info))
        else:
            payload["error"] = str(info)
    elif result.state == "SUCCESS":
        payload["result"] = result.result
        payload["error"] = None
    else:
        payload["result"] = getattr(result, "result", None)
        payload["error"] = None

    return jsonify(payload)

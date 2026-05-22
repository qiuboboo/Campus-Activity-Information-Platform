from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..services.crawler_service import crawl_data_source as sync_crawl
from ..services.crawler_service import crawl_mcp_source as sync_mcp_crawl
from ..services.data_source_service import (
    create_data_source,
    get_crawl_logs,
    get_data_source,
    list_data_sources,
    update_data_source,
)
from ..tasks.crawl_tasks import crawl_data_source_task
from ..utils.auth import roles_required

data_sources_bp = Blueprint("data_sources", __name__)


@data_sources_bp.route("/data-sources", methods=["GET"])
@jwt_required()
def get_all():
    sources = list_data_sources()
    return jsonify({"items": [s.to_dict() for s in sources]})


@data_sources_bp.route("/data-sources", methods=["POST"])
@roles_required("admin")
def create():
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    base_url = data.get("base_url", "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not base_url:
        return jsonify({"error": "base_url is required"}), 400

    try:
        ds = create_data_source(
            name=name,
            base_url=base_url,
            list_selector=data.get("list_selector"),
            content_selector=data.get("content_selector"),
            crawl_mode=data.get("crawl_mode", "basic"),
            enabled=data.get("enabled", True),
            source_level=data.get("source_level", "external"),
            owner=data.get("owner"),
            notes=data.get("notes"),
            allowed_domains=data.get("allowed_domains"),
            request_interval=data.get("request_interval"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(ds.to_dict()), 201


@data_sources_bp.route("/data-sources/<int:source_id>", methods=["GET"])
@jwt_required()
def get_one(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404
    return jsonify(ds.to_dict())


@data_sources_bp.route("/data-sources/<int:source_id>", methods=["PUT"])
@roles_required("admin")
def update(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404

    data = request.get_json(force=True)
    try:
        ds = update_data_source(
            source_id,
            name=data.get("name"),
            base_url=data.get("base_url"),
            list_selector=data.get("list_selector"),
            content_selector=data.get("content_selector"),
            crawl_mode=data.get("crawl_mode"),
            enabled=data.get("enabled"),
            source_level=data.get("source_level"),
            owner=data.get("owner"),
            notes=data.get("notes"),
            allowed_domains=data.get("allowed_domains"),
            request_interval=data.get("request_interval"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(ds.to_dict())


@data_sources_bp.route("/data-sources/<int:source_id>/crawl", methods=["POST"])
@roles_required("admin")
def crawl(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404

    data = request.get_json(silent=True) or {}
    is_sync = data.get("sync", False)

    user_id = int(get_jwt_identity())

    if is_sync:
        if ds.crawl_mode == "mcp":
            result = sync_mcp_crawl(source_id, user_id)
        else:
            result = sync_crawl(source_id, user_id)
        if not result["success"]:
            return jsonify({"error": result.get("error", "Crawl failed")}), 500
        return jsonify(result), 200

    if ds.crawl_mode == "mcp":
        result = sync_mcp_crawl(source_id, user_id)
        if not result["success"]:
            return jsonify({"error": result.get("error", "Crawl failed")}), 500
        return jsonify(result), 200

    task = crawl_data_source_task.delay(source_id, user_id)
    return (
        jsonify({
            "task_id": task.id,
            "status_url": f"/api/tasks/{task.id}",
        }),
        202,
    )


@data_sources_bp.route("/data-sources/<int:source_id>/logs", methods=["GET"])
@jwt_required()
def get_logs(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404

    logs = get_crawl_logs(source_id)
    return jsonify({"items": [log.to_dict() for log in logs]})

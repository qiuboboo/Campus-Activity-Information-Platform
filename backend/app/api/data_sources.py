from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Poster
from ..services.crawler_service import crawl_data_source as sync_crawl
from ..services.crawler_service import crawl_mcp_source as sync_mcp_crawl
from ..services.data_source_service import (
    create_crawl_log,
    create_data_source,
    delete_data_source,
    finish_crawl_log,
    get_crawl_logs,
    get_data_source,
    list_data_sources,
    update_data_source,
)
from ..services.dedup_service import check_duplicates
from ..services.poster_service import auto_extract_fields
from ..services.weixin_search_service import search_and_fetch as weixin_search_and_fetch
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
    base_url = (data.get("base_url") or data.get("url") or "").strip()

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
<<<<<<< Updated upstream
            base_url=data.get("base_url") or data.get("url"),
=======
            base_url=data.get("base_url", data.get("url")),
>>>>>>> Stashed changes
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


@data_sources_bp.route("/data-sources/<int:source_id>", methods=["PATCH"])
@roles_required("admin")
def patch(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404
    data = request.get_json(force=True)
    try:
        ds = update_data_source(
            source_id,
            name=data.get("name"),
            base_url=data.get("base_url") or data.get("url"),
            enabled=data.get("enabled"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(ds.to_dict())


@data_sources_bp.route("/data-sources/<int:source_id>", methods=["DELETE"])
@roles_required("admin")
def delete(source_id: int):
    if not delete_data_source(source_id):
        return jsonify({"error": "Data source not found"}), 404
    return jsonify({"success": True, "message": "Data source deleted"}), 200


@data_sources_bp.post("/data-sources/<int:source_id>/preview-crawl")
@roles_required("admin")
def preview_crawl(source_id: int):
    """Crawl + extract fields without saving — returns candidate list for review."""
    from ..services.crawler_service import collect_crawl_candidates

    limit = min(int(request.args.get("limit", 10)), 50)
    try:
        candidates = collect_crawl_candidates(source_id, limit=limit)
    except ValueError:
        return jsonify({"message": "Data source not found"}), 404
    return jsonify({"items": candidates, "total": len(candidates)})


@data_sources_bp.route("/data-sources/<int:source_id>/crawl", methods=["POST"])
@roles_required("admin")
def crawl(source_id: int):
    ds = get_data_source(source_id)
    if ds is None:
        return jsonify({"error": "Data source not found"}), 404

    data = request.get_json(silent=True) or {}
    is_sync = data.get("sync", False)

    user_id = int(get_jwt_identity())

    # WeChat search — fast enough for sync, uses base_url as search query
    if ds.crawl_mode == "weixin":
        results = weixin_search_and_fetch(ds.base_url, max_results=5)

        log = create_crawl_log(source_id)
        created = 0
        for r in results:
            dup = check_duplicates(source_url=r["source_url"])
            if dup:
                continue
            extracted = auto_extract_fields(r["title"], r["content"])
            poster = Poster(
                title=r["title"],
                raw_text=r["content"],
                summary=extracted.get("summary", r["title"]),
                event_time=extracted.get("event_time"),
                location=extracted.get("location"),
                organizer=extracted.get("organizer", "微信公众号"),
                status="draft",
                source_type="crawl",
                source_url=r["source_url"],
                created_by=user_id,
            )
            db.session.add(poster)
            created += 1
        db.session.commit()
        finish_crawl_log(log, "success",
            message=f"微信搜索完成，找到 {len(results)} 条，新建 {created} 条",
            pages_found=len(results), drafts_created=created)
        return jsonify({"success": True, "message": f"微信搜索完成，找到 {len(results)} 条，新建 {created} 条"}), 200

    # Sync path — also used for mcp which is fast enough for sync
    if is_sync or ds.crawl_mode == "mcp":
        if ds.crawl_mode == "mcp":
            result = sync_mcp_crawl(source_id, user_id)
        else:
            result = sync_crawl(source_id, user_id)
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

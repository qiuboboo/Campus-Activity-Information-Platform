from datetime import datetime

from flask import Blueprint, jsonify
from sqlalchemy import func

from ..models import CrawlLog, DataSource, KnowledgeNode, Poster, PosterLink
from ..utils.auth import roles_required

export_bp = Blueprint("export", __name__)


@export_bp.get("/export/posters.json")
@roles_required("admin")
def export_posters():
    posters = Poster.query.order_by(Poster.created_at.desc()).all()
    items = []
    for p in posters:
        d = p.to_dict()
        # Strip raw_text to reduce export size; keep summary
        d.pop("raw_text", None)
        d.pop("password_hash", None)
        items.append(d)
    return jsonify({"count": len(items), "items": items})


@export_bp.get("/export/knowledge.json")
@roles_required("admin")
def export_knowledge():
    nodes = KnowledgeNode.query.order_by(KnowledgeNode.created_at.desc()).all()
    return jsonify({
        "count": len(nodes),
        "items": [n.to_dict() for n in nodes],
    })


@export_bp.get("/export/crawl-report.json")
@roles_required("admin")
def export_crawl_report():
    logs = CrawlLog.query.order_by(CrawlLog.created_at.desc()).limit(100).all()
    return jsonify({
        "count": len(logs),
        "items": [log.to_dict() for log in logs],
    })


@export_bp.get("/demo/summary")
@roles_required("admin")
def demo_summary():
    total_posters = Poster.query.count()
    published = Poster.query.filter_by(status="published").count()
    draft = Poster.query.filter_by(status="draft").count()
    rejected = Poster.query.filter_by(status="rejected").count()

    total_nodes = KnowledgeNode.query.count()
    total_links = PosterLink.query.count()
    total_sources = DataSource.query.count()

    last_crawl = (
        CrawlLog.query.order_by(CrawlLog.created_at.desc()).first()
    )
    last_crawl_info = None
    if last_crawl is not None:
        last_crawl_info = {
            "id": last_crawl.id,
            "data_source_id": last_crawl.data_source_id,
            "status": last_crawl.status,
            "pages_found": last_crawl.pages_found,
            "pages_succeeded": last_crawl.pages_succeeded,
            "pages_failed": last_crawl.pages_failed,
            "duplicates_skipped": last_crawl.duplicates_skipped,
            "drafts_created": last_crawl.drafts_created,
            "average_quality_score": last_crawl.average_quality_score,
            "started_at": last_crawl.started_at.isoformat(),
            "finished_at": last_crawl.finished_at.isoformat() if last_crawl.finished_at else None,
        }

    return jsonify({
        "pending": Poster.query.filter_by(status="pending_review").count(),
        "published": published,
        "sources": total_sources,
        "failed_tasks": 0,
        "posters": {
            "total": total_posters,
            "published": published,
            "draft": draft,
            "rejected": rejected,
        },
        "knowledge_nodes": total_nodes,
        "poster_links": total_links,
        "data_sources": total_sources,
        "last_crawl": last_crawl_info,
    })

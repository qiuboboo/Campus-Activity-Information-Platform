"""Dictionary management API — controlled vocabulary for place/org/topic."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..services.dict_manager import (
    add_entry,
    delete_entry,
    list_entries,
    seed_builtin_aliases,
    update_entry,
)
from ..utils.auth import roles_required

dicts_bp = Blueprint("dicts", __name__)


@dicts_bp.get("/dict/<category>")
@jwt_required()
def list_category(category: str):
    """List entries in a dictionary category (place, org, topic)."""
    q = request.args.get("q", "").strip() or None
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 50)), 200), 1)

    items, total = list_entries(category=category, query=q, page=page, per_page=per_page)
    return jsonify({
        "category": category,
        "items": [item.to_dict() for item in items],
        "page": page,
        "per_page": per_page,
        "total": total,
    })


@dicts_bp.post("/dict/<category>")
@roles_required("admin")
def create_entry(category: str):
    """Create a new dictionary entry."""
    data = request.get_json(silent=True) or {}
    standard_name = (data.get("standard_name") or "").strip()
    if not standard_name:
        return jsonify({"error": "standard_name is required"}), 400

    try:
        entry = add_entry(
            category=category,
            standard_name=standard_name,
            aliases=data.get("aliases"),
            description=data.get("description"),
        )
        db.session.commit()
        return jsonify({"item": entry.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@dicts_bp.put("/dict/<category>/<int:entry_id>")
@roles_required("admin")
def edit_entry(category: str, entry_id: int):
    """Update a dictionary entry."""
    data = request.get_json(silent=True) or {}
    entry = update_entry(entry_id, category=category, **data)
    if entry is None:
        return jsonify({"error": "Entry not found"}), 404
    db.session.commit()
    return jsonify({"item": entry.to_dict()})


@dicts_bp.delete("/dict/<category>/<int:entry_id>")
@roles_required("admin")
def remove_entry(category: str, entry_id: int):
    """Delete a dictionary entry."""
    if delete_entry(entry_id):
        db.session.commit()
        return jsonify({"deleted": True}), 200
    return jsonify({"error": "Entry not found"}), 404


@dicts_bp.post("/dict/seed")
@roles_required("admin")
def seed_entries():
    """Insert built-in alias mappings into the database."""
    count = seed_builtin_aliases()
    db.session.commit()
    return jsonify({"seeded": count}), 201 if count else 200


@dicts_bp.get("/dict/<category>/suggestions")
@roles_required("admin")
def get_suggestions(category: str):
    """Return values from published posters that are not yet in the dictionary."""
    if category not in ("place", "org", "topic"):
        return jsonify({"message": "invalid category"}), 400
    suggestions = suggest_from_posters(category)
    return jsonify({"items": suggestions, "total": len(suggestions)})

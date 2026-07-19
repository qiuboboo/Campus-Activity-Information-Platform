<<<<<<< Updated upstream
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename


uploads_bp = Blueprint("uploads", __name__)

_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".doc", ".docx", ".xls", ".xlsx"}
_MAX_SIZE = 10 * 1024 * 1024


def _upload_dir() -> Path:
    path = Path(current_app.instance_path) / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path
=======
"""Authenticated local attachment storage for activity publishers."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import ActivityAttachment


uploads_bp = Blueprint("uploads", __name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _is_admin() -> bool:
    return get_jwt().get("role") == "admin"


def _storage_path(attachment: ActivityAttachment) -> Path:
    return Path(current_app.config["UPLOAD_DIR"]) / attachment.stored_name


def _can_access(attachment: ActivityAttachment, user_id: int | None) -> bool:
    if attachment.poster and attachment.poster.status == "published":
        return True
    return bool(user_id and (user_id == attachment.owner_id or _is_admin()))
>>>>>>> Stashed changes


@uploads_bp.post("/uploads")
@jwt_required()
<<<<<<< Updated upstream
def upload_file():
    file = request.files.get("file")
    if file is None:
        return jsonify({"message": "file is required"}), 400

    original_name = secure_filename(file.filename or "upload")
    suffix = Path(original_name).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        return jsonify({"message": "unsupported file type"}), 422

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_SIZE:
        return jsonify({"message": "file too large"}), 413

    upload_id = f"{uuid4().hex}{suffix}"
    file.save(_upload_dir() / upload_id)
    return jsonify({
        "id": upload_id,
        "name": original_name,
        "url": f"/api/uploads/{upload_id}/content",
        "mime_type": file.mimetype,
        "size": size,
    }), 201


@uploads_bp.get("/uploads/<path:upload_id>/content")
def upload_content(upload_id: str):
    return send_from_directory(_upload_dir(), upload_id)


@uploads_bp.delete("/uploads/<path:upload_id>")
@jwt_required()
def delete_upload(upload_id: str):
    path = _upload_dir() / upload_id
    if path.exists():
=======
def upload_attachment():
    user_id = int(get_jwt_identity())
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"message": "file is required"}), 400
    if file.mimetype not in ALLOWED_MIME_TYPES:
        return jsonify({"message": "unsupported attachment type"}), 415

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > current_app.config["MAX_UPLOAD_SIZE"]:
        return jsonify({"message": "attachment exceeds the size limit"}), 413

    original_name = secure_filename(file.filename) or "attachment"
    stored_name = f"{uuid4().hex}_{original_name}"
    storage = Path(current_app.config["UPLOAD_DIR"])
    storage.mkdir(parents=True, exist_ok=True)
    file.save(storage / stored_name)
    attachment = ActivityAttachment(
        owner_id=user_id,
        original_name=original_name,
        stored_name=stored_name,
        mime_type=file.mimetype,
        size=size,
    )
    db.session.add(attachment)
    db.session.commit()
    return jsonify(attachment.to_dict()), 201


@uploads_bp.get("/uploads/<string:attachment_id>/content")
def download_attachment(attachment_id: str):
    attachment = ActivityAttachment.query.get_or_404(attachment_id)
    user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        user_id = int(identity) if identity else None
    except Exception:
        pass
    if not _can_access(attachment, user_id):
        return jsonify({"message": "attachment not found"}), 404
    path = _storage_path(attachment)
    if not path.is_file():
        return jsonify({"message": "attachment file is missing"}), 404
    return send_file(path, mimetype=attachment.mime_type, download_name=attachment.original_name)


@uploads_bp.delete("/uploads/<string:attachment_id>")
@jwt_required()
def delete_attachment(attachment_id: str):
    attachment = ActivityAttachment.query.get_or_404(attachment_id)
    if attachment.owner_id != int(get_jwt_identity()) and not _is_admin():
        return jsonify({"message": "permission denied"}), 403
    path = _storage_path(attachment)
    db.session.delete(attachment)
    db.session.commit()
    if path.is_file():
>>>>>>> Stashed changes
        path.unlink()
    return jsonify({"success": True})

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


@uploads_bp.post("/uploads")
@jwt_required()
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
        path.unlink()
    return jsonify({"success": True})

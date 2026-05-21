from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import User
from ..utils.ratelimit import limiter
from ..services.captcha_service import create_captcha, validate_captcha as _check_captcha


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/captcha")
@limiter.limit("30 per minute")
def captcha_image():
    """Return a CAPTCHA image (PNG).  The captcha_token is returned in a header."""
    from io import BytesIO

    token, image_bytes = create_captcha()
    resp = send_file(BytesIO(image_bytes), mimetype="image/png")
    resp.headers["X-Captcha-Token"] = token
    return resp


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    role = (payload.get("role") or "viewer").strip()
    captcha_token = payload.get("captcha_token") or ""
    captcha_code = payload.get("captcha_code") or ""

    if not username or not password:
        return jsonify({"message": "username and password are required"}), 400

    if not _check_captcha(captcha_token, captcha_code):
        return jsonify({"message": "invalid or missing captcha"}), 400
    if len(username) < 2 or len(username) > 50:
        return jsonify({"message": "username must be 2-50 characters"}), 400
    if len(password) < 6:
        return jsonify({"message": "password must be at least 6 characters"}), 400
    if role not in ("viewer", "publisher"):
        return jsonify({"message": "role must be 'viewer' or 'publisher'"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "username already exists"}), 409

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "username": user.username},
    )
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    captcha_token = payload.get("captcha_token") or ""
    captcha_code = payload.get("captcha_code") or ""

    if not username or not password:
        return jsonify({"message": "username and password are required"}), 400

    if not _check_captcha(captcha_token, captcha_code):
        return jsonify({"message": "invalid or missing captcha"}), 400

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"message": "invalid credentials"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "username": user.username},
    )
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify({"user": user.to_dict()})

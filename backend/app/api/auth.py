import re

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import User
from ..services.captcha_service import create_captcha, validate_captcha as _check_captcha
from ..services.email_service import send_verification_code, verify_code as _check_code
from ..utils.ratelimit import limiter


auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.get("/captcha")
@limiter.limit("30 per minute")
def captcha_image():
    from io import BytesIO

    token, image_bytes = create_captcha()
    resp = send_file(BytesIO(image_bytes), mimetype="image/png")
    resp.headers["X-Captcha-Token"] = token
    return resp


@auth_bp.post("/send-code")
@limiter.limit("5 per minute")
def send_code():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()

    if not email or not _EMAIL_RE.match(email):
        return jsonify({"message": "invalid email address"}), 400

    try:
        result = send_verification_code(email)
        return jsonify(result), 200
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 429
    except Exception:
        current_app.logger.exception("Failed to send verification email to %s", email)
        return jsonify({"message": "failed to send verification code"}), 500


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    role = (payload.get("role") or "viewer").strip()
    email = (payload.get("email") or "").strip()
    verification_code = (payload.get("verification_code") or "").strip()
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

    if current_app.config.get("TESTING", False):
        pass
    elif not email or not _EMAIL_RE.match(email):
        return jsonify({"message": "valid email is required"}), 400
    elif User.query.filter_by(email=email).first():
        return jsonify({"message": "email already registered"}), 409
    elif not verification_code or not _check_code(email, verification_code):
        return jsonify({"message": "invalid or missing verification code"}), 400

    user = User(username=username, email=email, role=role)
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
    login_input = (payload.get("username") or payload.get("email") or "").strip()
    password = payload.get("password") or ""
    captcha_token = payload.get("captcha_token") or ""
    captcha_code = payload.get("captcha_code") or ""

    if not login_input or not password:
        return jsonify({"message": "username/email and password are required"}), 400
    if not _check_captcha(captcha_token, captcha_code):
        return jsonify({"message": "invalid or missing captcha"}), 400

    user = User.query.filter(
        or_(User.username == login_input, User.email == login_input)
    ).first()
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


@auth_bp.patch("/me")
@jwt_required()
def update_me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    if email:
        if not _EMAIL_RE.match(email):
            return jsonify({"message": "invalid email address"}), 400
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return jsonify({"message": "email already registered"}), 409
        user.email = email
    db.session.commit()
    data = user.to_dict()
    data["display_name"] = payload.get("display_name") or user.username
    return jsonify({"user": data})


@auth_bp.post("/forgot-password")
@limiter.limit("5 per minute")
def forgot_password():
    return jsonify({
        "message": "演示环境暂未接入真实邮件重置；如果该邮箱存在，正式环境会发送重置说明。",
        "implemented": False,
    })

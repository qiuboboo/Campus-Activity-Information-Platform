import re
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
<<<<<<< Updated upstream
from ..models import User
=======
from ..models import PublisherApplication, User
from ..utils.auth import roles_required
from ..utils.ratelimit import limiter
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    if role not in ("viewer", "publisher"):
        return jsonify({"message": "role must be 'viewer' or 'publisher'"}), 400
=======
    if role != "viewer":
        return jsonify({"message": "new accounts must register as viewers and apply for publisher access"}), 400

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    user = User.query.get_or_404(int(get_jwt_identity()))
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
=======
    """Update the editable fields exposed by the profile page."""
    user = User.query.get_or_404(int(get_jwt_identity()))
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()

>>>>>>> Stashed changes
    if email:
        if not _EMAIL_RE.match(email):
            return jsonify({"message": "invalid email address"}), 400
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return jsonify({"message": "email already registered"}), 409
        user.email = email
<<<<<<< Updated upstream
    db.session.commit()
    data = user.to_dict()
    data["display_name"] = payload.get("display_name") or user.username
    return jsonify({"user": data})
=======

    db.session.commit()
    return jsonify({"user": user.to_dict()})
>>>>>>> Stashed changes


@auth_bp.post("/forgot-password")
@limiter.limit("5 per minute")
<<<<<<< Updated upstream
def forgot_password():
    return jsonify({
        "message": "演示环境暂未接入真实邮件重置；如果该邮箱存在，正式环境会发送重置说明。",
        "implemented": False,
    })
=======
def request_password_reset():
    """Send a reset code without revealing whether an account exists."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    if not email or not _EMAIL_RE.match(email):
        return jsonify({"message": "invalid email address"}), 400
    user = User.query.filter_by(email=email).first()
    result = {"message": "如果该邮箱已注册，重置验证码已发送"}
    if user is not None:
        try:
            sent = send_verification_code(email, purpose="password_reset")
            result.update({key: value for key, value in sent.items() if key in {"expires_in", "code"}})
        except RuntimeError as exc:
            return jsonify({"message": str(exc)}), 429
        except Exception:
            current_app.logger.exception("Failed to send password reset code")
    return jsonify(result), 200


@auth_bp.post("/reset-password")
@limiter.limit("5 per minute")
def reset_password():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    code = (payload.get("verification_code") or "").strip()
    password = payload.get("password") or ""
    if not email or not _EMAIL_RE.match(email) or not code:
        return jsonify({"message": "email and verification code are required"}), 400
    if len(password) < 6:
        return jsonify({"message": "password must be at least 6 characters"}), 400
    user = User.query.filter_by(email=email).first()
    if user is None or not _check_code(email, code, purpose="password_reset"):
        return jsonify({"message": "invalid or expired verification code"}), 400
    user.set_password(password)
    db.session.commit()
    return jsonify({"message": "password reset successfully"})


@auth_bp.get("/publisher-applications/mine")
@jwt_required()
def my_publisher_application():
    application = PublisherApplication.query.filter_by(user_id=int(get_jwt_identity())).first()
    return jsonify({"item": application.to_dict() if application else None})


@auth_bp.post("/publisher-applications")
@jwt_required()
def apply_for_publisher():
    user = User.query.get_or_404(int(get_jwt_identity()))
    if user.role in ("publisher", "admin"):
        return jsonify({"message": "user already has publisher access"}), 400
    payload = request.get_json(silent=True) or {}
    reason = (payload.get("reason") or "").strip()
    if len(reason) > 500:
        return jsonify({"message": "application reason is too long"}), 400

    application = PublisherApplication.query.filter_by(user_id=user.id).first()
    if application and application.status == "pending":
        return jsonify({"item": application.to_dict(), "message": "application is already pending"}), 200
    if application is None:
        application = PublisherApplication(user_id=user.id, reason=reason or None)
        db.session.add(application)
    else:
        application.reason = reason or None
        application.status = "pending"
        application.review_comment = None
        application.reviewed_at = None
    db.session.commit()
    return jsonify({"item": application.to_dict()}), 201


@auth_bp.get("/publisher-applications")
@roles_required("admin")
def list_publisher_applications():
    status = (request.args.get("status") or "pending").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = max(min(request.args.get("per_page", 20, type=int), 100), 1)
    query = PublisherApplication.query.order_by(PublisherApplication.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [item.to_dict() for item in result.items], "page": page, "per_page": per_page, "total": result.total})


@auth_bp.post("/publisher-applications/<int:application_id>/review")
@roles_required("admin")
def review_publisher_application(application_id: int):
    application = PublisherApplication.query.get_or_404(application_id)
    if application.status != "pending":
        return jsonify({"message": "application has already been reviewed"}), 400
    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "").strip().lower()
    comment = (payload.get("comment") or "").strip()
    if action not in ("approve", "reject"):
        return jsonify({"message": "action must be approve or reject"}), 400

    application.status = "approved" if action == "approve" else "rejected"
    application.review_comment = comment or None
    application.reviewed_at = datetime.utcnow()
    if action == "approve":
        application.user.role = "publisher"
    db.session.commit()
    return jsonify({"item": application.to_dict()})
>>>>>>> Stashed changes

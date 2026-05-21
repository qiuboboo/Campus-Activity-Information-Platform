"""API blueprint for subscriptions and notifications."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Notification, Subscription
from ..utils.auth import roles_required

subscriptions_bp = Blueprint("subscriptions", __name__)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------


@subscriptions_bp.post("")
@jwt_required()
def create_subscription():
    """Create a subscription (by node_id or keyword)."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    node_id = payload.get("node_id")
    keyword = (payload.get("keyword") or "").strip()
    notify_method = (payload.get("notify_method") or "platform").strip()

    if node_id is not None:
        node_id = int(node_id)

    if not node_id and not keyword:
        return jsonify({"message": "node_id or keyword is required"}), 400
    if node_id and keyword:
        return jsonify({"message": "provide either node_id or keyword, not both"}), 400

    existing = Subscription.query.filter_by(
        user_id=user_id,
        node_id=node_id,
        keyword=keyword or None,
    ).first()
    if existing:
        return jsonify({"item": existing.to_dict()}), 200

    sub = Subscription(
        user_id=user_id,
        node_id=node_id,
        keyword=keyword or None,
        notify_method=notify_method,
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({"item": sub.to_dict()}), 201


@subscriptions_bp.get("")
@jwt_required()
def list_subscriptions():
    """List current user's subscriptions."""
    user_id = int(get_jwt_identity())
    subs = Subscription.query.filter_by(user_id=user_id).order_by(
        Subscription.created_at.desc()
    ).all()
    return jsonify({"items": [s.to_dict() for s in subs], "total": len(subs)})


@subscriptions_bp.delete("/<int:sub_id>")
@jwt_required()
def delete_subscription(sub_id: int):
    """Cancel a subscription."""
    user_id = int(get_jwt_identity())
    sub = Subscription.query.get_or_404(sub_id)
    if sub.user_id != user_id:
        return jsonify({"message": "permission denied"}), 403
    db.session.delete(sub)
    db.session.commit()
    return jsonify({"message": "subscription cancelled"}), 200


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@subscriptions_bp.get("/notifications")
@jwt_required()
def list_notifications():
    """List current user's notifications, optional is_read filter."""
    user_id = int(get_jwt_identity())
    is_read = request.args.get("is_read", type=str)
    query = Notification.query.filter_by(user_id=user_id)
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == "true")
    notifications = query.order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({
        "items": [n.to_dict() for n in notifications],
        "total": len(notifications),
        "unread_count": unread_count,
    })


@subscriptions_bp.put("/notifications/<int:notif_id>/read")
@jwt_required()
def mark_notification_read(notif_id: int):
    """Mark a single notification as read."""
    user_id = int(get_jwt_identity())
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user_id:
        return jsonify({"message": "permission denied"}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({"item": notif.to_dict()})


@subscriptions_bp.put("/notifications/read-all")
@jwt_required()
def mark_all_notifications_read():
    """Mark all of the current user's notifications as read."""
    user_id = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify({"message": f"marked {count} notifications as read", "updated": count})

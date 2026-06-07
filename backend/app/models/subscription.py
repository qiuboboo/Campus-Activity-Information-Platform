from datetime import datetime

from ..extensions import db
from .base import TimestampMixin


class Subscription(TimestampMixin, db.Model):
    """User subscription to a knowledge node or keyword."""

    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey("knowledge_nodes.id"), nullable=True)
    keyword = db.Column(db.String(200), nullable=True)
    notify_method = db.Column(db.String(20), default="platform", nullable=False)

    user = db.relationship("User", back_populates="subscriptions")
    node = db.relationship("KnowledgeNode")

    __table_args__ = (
        db.CheckConstraint(
            "node_id IS NOT NULL OR keyword IS NOT NULL",
            name="ck_subscription_target",
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "node_id": self.node_id,
            "keyword": self.keyword,
            "notify_method": self.notify_method,
            "node": self.node.to_dict() if self.node else None,
            "created_at": self.created_at.isoformat(),
        }


class Notification(db.Model):
    """In-platform notification triggered by subscription match."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")
    poster = db.relationship("Poster")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "poster_id": self.poster_id,
            "title": self.title,
            "body": self.body,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "poster": {"id": self.poster.id, "title": self.poster.title} if self.poster else None,
        }

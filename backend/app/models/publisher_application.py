from ..extensions import db
from .base import TimestampMixin

class PublisherApplication(TimestampMixin, db.Model):
    """A viewer's request to gain the publisher role."""

    __tablename__ = "publisher_applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False)
    review_comment = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="publisher_applications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "email": self.user.email if self.user else None,
            "reason": self.reason,
            "status": self.status,
            "review_comment": self.review_comment,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }



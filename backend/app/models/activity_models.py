from uuid import uuid4

from ..extensions import db
from .base import TimestampMixin

class ActivityRegistration(TimestampMixin, db.Model):
    """A user's submitted registration form for an activity poster."""

    __tablename__ = "activity_registrations"

    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(100), nullable=False)
    # Kept separate from the account email: this is the contact address the
    # attendee explicitly provided on this registration form.
    contact_email = db.Column(db.String(120), nullable=True)

    poster = db.relationship("Poster", back_populates="registrations")
    user = db.relationship("User", back_populates="activity_registrations")

    __table_args__ = (
        db.UniqueConstraint("poster_id", "user_id", name="uq_activity_registration_user"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "email": self.contact_email or (self.user.email if self.user else None),
            "name": self.name,
            "student_id": self.student_id,
            "college": self.college,
            "registered_at": self.created_at.isoformat(),
        }


class ActivityFavorite(TimestampMixin, db.Model):
    """A user's saved activity."""

    __tablename__ = "activity_favorites"

    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    poster = db.relationship("Poster", back_populates="favorites")
    user = db.relationship("User", back_populates="activity_favorites")

    __table_args__ = (
        db.UniqueConstraint("poster_id", "user_id", name="uq_activity_favorite_user"),
    )


class ActivityAttachment(TimestampMixin, db.Model):
    """A locally stored attachment, optionally linked to one activity."""

    __tablename__ = "activity_attachments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=True, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)

    owner = db.relationship("User", back_populates="uploads")
    poster = db.relationship("Poster", back_populates="attachments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.original_name,
            "url": f"/api/uploads/{self.id}/content",
            "mime_type": self.mime_type,
            "size": self.size,
        }



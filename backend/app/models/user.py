from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from .base import TimestampMixin


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="viewer", nullable=False)

    posters = db.relationship("Poster", back_populates="creator", lazy=True)
    subscriptions = db.relationship(
        "Subscription", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )
    calendar_events = db.relationship(
        "UserCalendarEvent", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )
    audit_logs = db.relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id", lazy=True
    )
    activity_registrations = db.relationship(
        "ActivityRegistration", back_populates="user", lazy=True,
        cascade="all, delete-orphan",
    )
    activity_favorites = db.relationship(
        "ActivityFavorite", back_populates="user", lazy=True,
        cascade="all, delete-orphan",
    )
    uploads = db.relationship(
        "ActivityAttachment", back_populates="owner", lazy=True,
        cascade="all, delete-orphan",
    )
    publisher_applications = db.relationship(
        "PublisherApplication", back_populates="user", lazy=True,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }

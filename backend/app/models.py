from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="viewer", nullable=False)

    posters = db.relationship("Poster", back_populates="creator", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class Poster(TimestampMixin, db.Model):
    __tablename__ = "posters"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    event_time = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    organizer = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(30), default="draft", nullable=False)
    source_type = db.Column(db.String(30), default="manual", nullable=False)
    source_url = db.Column(db.Text, nullable=True)
    review_comment = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    creator = db.relationship("User", back_populates="posters")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "raw_text": self.raw_text,
            "summary": self.summary,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "location": self.location,
            "organizer": self.organizer,
            "status": self.status,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "review_comment": self.review_comment,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

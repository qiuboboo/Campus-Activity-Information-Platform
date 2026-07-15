from ..extensions import db
from .base import TimestampMixin


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
    duplicate_group_key = db.Column(db.String(64), nullable=True, index=True)
    source_fingerprint = db.Column(db.String(64), nullable=True, index=True)
    quality_score = db.Column(db.Integer, nullable=True)
    quality_notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)
    activity_type = db.Column(db.String(50), nullable=True)
    content_html = db.Column(db.Text, nullable=True)
    cover_image_url = db.Column(db.Text, nullable=True)
    last_crawled_at = db.Column(db.DateTime, nullable=True)
    embedding = db.Column(db.Text, nullable=True)

    creator = db.relationship("User", back_populates="posters")
    nodes = db.relationship(
        "PosterNode",
        back_populates="poster",
        cascade="all, delete-orphan",
        lazy=True,
    )
    outgoing_links = db.relationship(
        "PosterLink",
        foreign_keys="PosterLink.from_poster_id",
        back_populates="from_poster",
        cascade="all, delete-orphan",
        lazy=True,
    )
    incoming_links = db.relationship(
        "PosterLink",
        foreign_keys="PosterLink.to_poster_id",
        back_populates="to_poster",
        cascade="all, delete-orphan",
        lazy=True,
    )

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
            "duplicate_group_key": self.duplicate_group_key,
            "source_fingerprint": self.source_fingerprint,
            "quality_score": self.quality_score,
            "quality_notes": self.quality_notes,
            "tags": self.tags,
            "activity_type": self.activity_type,
            "content_html": self.content_html,
            "cover_image_url": self.cover_image_url,
            "last_crawled_at": self.last_crawled_at.isoformat() if self.last_crawled_at else None,
            "embedding": self.embedding,
        }

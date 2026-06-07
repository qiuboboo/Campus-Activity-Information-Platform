from datetime import datetime

from ..extensions import db


class UserCalendarEvent(db.Model):
    """Records a user adding a poster to their personal calendar."""

    __tablename__ = "user_calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="calendar_events")
    poster = db.relationship("Poster")

    __table_args__ = (
        db.UniqueConstraint("user_id", "poster_id", name="uq_user_calendar_event"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "poster_id": self.poster_id,
            "added_at": self.added_at.isoformat(),
            "poster": self.poster.to_dict() if self.poster else None,
        }

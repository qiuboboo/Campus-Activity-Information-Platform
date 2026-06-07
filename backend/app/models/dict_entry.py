from ..extensions import db
from .base import TimestampMixin


class DictEntry(TimestampMixin, db.Model):
    """Controlled vocabulary entry for location/organizer/topic normalization."""

    __tablename__ = "dict_entries"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False, index=True)
    standard_name = db.Column(db.String(200), nullable=False)
    aliases = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("category", "standard_name", name="uq_dict_category_name"),
    )

    def alias_list(self) -> list[str]:
        if not self.aliases:
            return []
        return [a.strip() for a in self.aliases.split(",") if a.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "standard_name": self.standard_name,
            "aliases": self.aliases,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

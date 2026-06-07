from ..extensions import db
from .base import TimestampMixin


class KnowledgeNode(TimestampMixin, db.Model):
    __tablename__ = "knowledge_nodes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    alias = db.Column(db.Text, nullable=True)
    node_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.Text, nullable=True)
    embedding = db.Column(db.Text, nullable=True)

    posters = db.relationship(
        "PosterNode",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy=True,
    )

    __table_args__ = (
        db.UniqueConstraint("name", "node_type", name="uq_knowledge_nodes_name_type"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "node_type": self.node_type,
            "description": self.description,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "embedding": self.embedding,
        }


class PosterNode(db.Model):
    __tablename__ = "poster_node"

    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey("knowledge_nodes.id"), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)
    matched_by = db.Column(db.String(30), default="rule", nullable=False)

    poster = db.relationship("Poster", back_populates="nodes")
    node = db.relationship("KnowledgeNode", back_populates="posters")

    __table_args__ = (
        db.UniqueConstraint("poster_id", "node_id", "relation_type", name="uq_poster_node_relation"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "poster_id": self.poster_id,
            "node_id": self.node_id,
            "relation_type": self.relation_type,
            "matched_by": self.matched_by,
            "node": self.node.to_dict() if self.node else None,
        }


class PosterLink(TimestampMixin, db.Model):
    __tablename__ = "poster_links"

    id = db.Column(db.Integer, primary_key=True)
    from_poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    to_poster_id = db.Column(db.Integer, db.ForeignKey("posters.id"), nullable=False)
    link_type = db.Column(db.String(50), nullable=False)
    created_by_rule = db.Column(db.String(100), nullable=False)

    from_poster = db.relationship(
        "Poster",
        foreign_keys=[from_poster_id],
        back_populates="outgoing_links",
    )
    to_poster = db.relationship(
        "Poster",
        foreign_keys=[to_poster_id],
        back_populates="incoming_links",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "from_poster_id",
            "to_poster_id",
            "link_type",
            name="uq_poster_link_type",
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_poster_id": self.from_poster_id,
            "to_poster_id": self.to_poster_id,
            "link_type": self.link_type,
            "created_by_rule": self.created_by_rule,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "to_poster": self.to_poster.to_dict() if self.to_poster else None,
        }

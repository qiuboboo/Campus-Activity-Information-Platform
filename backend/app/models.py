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
    audit_logs = db.relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id", lazy=True
    )

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
    duplicate_group_key = db.Column(db.String(64), nullable=True, index=True)
    source_fingerprint = db.Column(db.String(64), nullable=True, index=True)
    quality_score = db.Column(db.Integer, nullable=True)
    quality_notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)
    activity_type = db.Column(db.String(50), nullable=True)
    last_crawled_at = db.Column(db.DateTime, nullable=True)

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
            "last_crawled_at": self.last_crawled_at.isoformat() if self.last_crawled_at else None,
        }


class KnowledgeNode(TimestampMixin, db.Model):
    __tablename__ = "knowledge_nodes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    alias = db.Column(db.Text, nullable=True)
    node_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.Text, nullable=True)

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


class DataSource(TimestampMixin, db.Model):
    __tablename__ = "data_sources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    list_selector = db.Column(db.String(500), nullable=True)
    content_selector = db.Column(db.String(500), nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    crawl_mode = db.Column(db.String(20), default="basic", nullable=False)
    source_level = db.Column(db.String(20), default="external", nullable=False)
    owner = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # --- Crawler security ---
    allowed_domains = db.Column(db.Text, nullable=True)
    request_interval = db.Column(db.Integer, default=2, nullable=False)
    last_success_at = db.Column(db.DateTime, nullable=True)
    last_failure_at = db.Column(db.DateTime, nullable=True)
    last_error_message = db.Column(db.Text, nullable=True)

    crawl_logs = db.relationship(
        "CrawlLog",
        back_populates="data_source",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def get_allowed_domains(self) -> list[str]:
        if not self.allowed_domains:
            return []
        return [d.strip() for d in self.allowed_domains.split(",") if d.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "list_selector": self.list_selector,
            "content_selector": self.content_selector,
            "enabled": self.enabled,
            "crawl_mode": self.crawl_mode,
            "source_level": self.source_level,
            "owner": self.owner,
            "notes": self.notes,
            "allowed_domains": self.allowed_domains,
            "request_interval": self.request_interval,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_error_message": self.last_error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CrawlLog(TimestampMixin, db.Model):
    __tablename__ = "crawl_logs"

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)
    status = db.Column(db.String(20), default="running", nullable=False)
    message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    pages_found = db.Column(db.Integer, default=0, nullable=False)
    pages_succeeded = db.Column(db.Integer, default=0, nullable=False)
    pages_failed = db.Column(db.Integer, default=0, nullable=False)
    duplicates_skipped = db.Column(db.Integer, default=0, nullable=False)
    drafts_created = db.Column(db.Integer, default=0, nullable=False)
    average_quality_score = db.Column(db.Float, nullable=True)

    data_source = db.relationship("DataSource", back_populates="crawl_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "data_source_id": self.data_source_id,
            "status": self.status,
            "message": self.message,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "pages_found": self.pages_found,
            "pages_succeeded": self.pages_succeeded,
            "pages_failed": self.pages_failed,
            "duplicates_skipped": self.duplicates_skipped,
            "drafts_created": self.drafts_created,
            "average_quality_score": self.average_quality_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    actor = db.relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "summary": self.summary,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat(),
        }

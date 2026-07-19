<<<<<<< Updated upstream
"""Backward-compatible re-export. New code should import from ``app.models`` package directly."""

from .models import *  # noqa: F401, F403
=======
from datetime import datetime
from uuid import uuid4

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
        "ActivityRegistration",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    activity_favorites = db.relationship(
        "ActivityFavorite",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    uploads = db.relationship(
        "ActivityAttachment", back_populates="owner", lazy=True, cascade="all, delete-orphan"
    )
    publisher_applications = db.relationship(
        "PublisherApplication",
        back_populates="user",
        lazy=True,
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
    registrations = db.relationship(
        "ActivityRegistration",
        back_populates="poster",
        lazy=True,
        cascade="all, delete-orphan",
    )
    favorites = db.relationship(
        "ActivityFavorite",
        back_populates="poster",
        lazy=True,
        cascade="all, delete-orphan",
    )
    attachments = db.relationship("ActivityAttachment", back_populates="poster", lazy=True)

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
            "last_crawled_at": self.last_crawled_at.isoformat() if self.last_crawled_at else None,
            "embedding": self.embedding,
        }


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
            "url": self.base_url,
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


class Subscription(TimestampMixin, db.Model):
    """User subscription to a knowledge node or keyword.

    When a new poster is published, subscriptions are matched and
    notification records are created for the matching users.
    """

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
    """In-platform notification for a user, triggered by subscription match."""

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
            "read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "poster": {"id": self.poster.id, "title": self.poster.title} if self.poster else None,
        }


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


class DictEntry(TimestampMixin, db.Model):
    """Controlled vocabulary entry for location/organizer/topic normalization.

    Maps user-facing aliases to canonical ``standard_name`` values so that
    knowledge nodes and relationships are consistent.
    """

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
>>>>>>> Stashed changes

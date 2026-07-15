from datetime import datetime

from ..extensions import db
from .base import TimestampMixin


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
            "last_status": self.last_error_message or (
                "抓取成功" if self.last_success_at else "尚未抓取"
            ),
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

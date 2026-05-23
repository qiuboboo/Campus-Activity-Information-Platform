import re

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import CrawlLog, DataSource


def _validate_base_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url):
        raise ValueError("base_url must start with http:// or https://")
    return url


def list_data_sources() -> list[DataSource]:
    return DataSource.query.order_by(DataSource.created_at.desc()).all()


def get_data_source(data_source_id: int) -> DataSource | None:
    return DataSource.query.get(data_source_id)


def create_data_source(
    name: str,
    base_url: str,
    list_selector: str | None = None,
    content_selector: str | None = None,
    crawl_mode: str = "basic",
    enabled: bool = True,
    source_level: str = "external",
    owner: str | None = None,
    notes: str | None = None,
    allowed_domains: str | None = None,
    request_interval: int | None = None,
) -> DataSource:
    base_url = _validate_base_url(base_url)

    if crawl_mode not in ("basic", "mcp", "weixin"):
        raise ValueError(f"Unsupported crawl_mode '{crawl_mode}'. Use 'basic', 'mcp', or 'weixin'.")

    if source_level not in ("official", "internal", "external"):
        raise ValueError("source_level must be one of: official, internal, external")

    ds = DataSource(
        name=name.strip(),
        base_url=base_url,
        list_selector=list_selector.strip() if list_selector else None,
        content_selector=content_selector.strip() if content_selector else None,
        crawl_mode=crawl_mode,
        enabled=enabled,
        source_level=source_level,
        owner=owner.strip() if owner else None,
        notes=notes.strip() if notes else None,
        allowed_domains=allowed_domains.strip() if allowed_domains else None,
        request_interval=request_interval or 2,
    )
    db.session.add(ds)
    db.session.commit()
    return ds


def update_data_source(
    data_source_id: int,
    name: str | None = None,
    base_url: str | None = None,
    list_selector: str | None = None,
    content_selector: str | None = None,
    crawl_mode: str | None = None,
    enabled: bool | None = None,
    source_level: str | None = None,
    owner: str | None = None,
    notes: str | None = None,
    allowed_domains: str | None = None,
    request_interval: int | None = None,
) -> DataSource | None:
    ds = get_data_source(data_source_id)
    if ds is None:
        return None

    if name is not None:
        ds.name = name.strip()
    if base_url is not None:
        ds.base_url = _validate_base_url(base_url)
    if list_selector is not None:
        ds.list_selector = list_selector.strip() if list_selector else None
    if content_selector is not None:
        ds.content_selector = content_selector.strip() if content_selector else None
    if crawl_mode is not None:
        if crawl_mode not in ("basic", "mcp", "weixin"):
            raise ValueError(f"Unsupported crawl_mode '{crawl_mode}'. Use 'basic', 'mcp', or 'weixin'.")
        ds.crawl_mode = crawl_mode
    if enabled is not None:
        ds.enabled = enabled
    if source_level is not None:
        if source_level not in ("official", "internal", "external"):
            raise ValueError("source_level must be one of: official, internal, external")
        ds.source_level = source_level
    if owner is not None:
        ds.owner = owner.strip() if owner else None
    if notes is not None:
        ds.notes = notes.strip() if notes else None
    if allowed_domains is not None:
        ds.allowed_domains = allowed_domains.strip() if allowed_domains else None
    if request_interval is not None:
        ds.request_interval = request_interval

    db.session.commit()
    return ds


def delete_data_source(data_source_id: int) -> bool:
    """Delete a data source and its associated crawl logs."""
    ds = get_data_source(data_source_id)
    if ds is None:
        return False
    db.session.delete(ds)
    db.session.commit()
    return True


def set_enabled(data_source_id: int, enabled: bool) -> DataSource | None:
    ds = get_data_source(data_source_id)
    if ds is None:
        return None
    ds.enabled = enabled
    db.session.commit()
    return ds


def create_crawl_log(data_source_id: int) -> CrawlLog:
    log = CrawlLog(data_source_id=data_source_id, status="running")
    db.session.add(log)
    db.session.commit()
    return log


def finish_crawl_log(
    log: CrawlLog,
    status: str,
    message: str | None = None,
    pages_found: int = 0,
    pages_succeeded: int = 0,
    pages_failed: int = 0,
    duplicates_skipped: int = 0,
    drafts_created: int = 0,
    average_quality_score: float | None = None,
) -> None:
    from datetime import datetime

    log.status = status
    log.message = message
    log.finished_at = datetime.utcnow()
    log.pages_found = pages_found
    log.pages_succeeded = pages_succeeded
    log.pages_failed = pages_failed
    log.duplicates_skipped = duplicates_skipped
    log.drafts_created = drafts_created
    log.average_quality_score = average_quality_score
    db.session.commit()


def get_crawl_logs(data_source_id: int) -> list[CrawlLog]:
    return (
        CrawlLog.query.filter_by(data_source_id=data_source_id)
        .order_by(CrawlLog.created_at.desc())
        .all()
    )

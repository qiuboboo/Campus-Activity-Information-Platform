"""Unit tests for data_source_service."""

import pytest

from app.models import CrawlLog, DataSource
from app.services.data_source_service import (
    _validate_base_url,
    create_crawl_log,
    create_data_source,
    finish_crawl_log,
    get_crawl_logs,
    get_data_source,
    list_data_sources,
    set_enabled,
    update_data_source,
)


class TestValidateBaseUrl:
    def test_accepts_http(self):
        assert _validate_base_url("http://example.com") == "http://example.com"

    def test_accepts_https(self):
        assert _validate_base_url("https://example.edu.cn") == "https://example.edu.cn"

    def test_rejects_no_scheme(self):
        with pytest.raises(ValueError):
            _validate_base_url("example.com")

    def test_rejects_ftp(self):
        with pytest.raises(ValueError):
            _validate_base_url("ftp://example.com")


class TestCreateDataSource:
    def test_creates_valid_source(self, app):
        with app.app_context():
            ds = create_data_source(
                name="测试来源",
                base_url="https://example.edu.cn/news",
                list_selector="a.title",
                content_selector="div.content",
                allowed_domains="example.edu.cn",
            )
            assert ds.id is not None
            assert ds.name == "测试来源"
            assert ds.base_url == "https://example.edu.cn/news"
            assert ds.enabled is True
            assert ds.crawl_mode == "basic"

    def test_rejects_invalid_crawl_mode(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="crawl_mode"):
                create_data_source(
                    name="test",
                    base_url="https://example.edu.cn",
                    crawl_mode="invalid",
                )

    def test_rejects_invalid_source_level(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="source_level"):
                create_data_source(
                    name="test",
                    base_url="https://example.edu.cn",
                    source_level="unknown",
                )

    def test_creates_mcp_source(self, app):
        with app.app_context():
            ds = create_data_source(
                name="小红书",
                base_url="https://xiaohongshu.com",
                crawl_mode="mcp",
                source_level="external",
            )
            assert ds.crawl_mode == "mcp"


class TestGetDataSource:
    def test_returns_source_by_id(self, app, sample_data_source):
        with app.app_context():
            ds = get_data_source(sample_data_source.id)
            assert ds is not None
            assert ds.name == "校园网通知公告"

    def test_returns_none_for_missing(self, app):
        with app.app_context():
            assert get_data_source(99999) is None


class TestListDataSources:
    def test_lists_all_sources(self, app):
        with app.app_context():
            sources = list_data_sources()
            assert isinstance(sources, list)


class TestUpdateDataSource:
    def test_updates_fields(self, app, sample_data_source):
        with app.app_context():
            ds = update_data_source(sample_data_source.id, name="新名称")
            assert ds is not None
            assert ds.name == "新名称"

    def test_returns_none_for_missing(self, app):
        with app.app_context():
            assert update_data_source(99999, name="x") is None


class TestSetEnabled:
    def test_disables_data_source(self, app, sample_data_source):
        with app.app_context():
            ds = set_enabled(sample_data_source.id, False)
            assert ds.enabled is False

    def test_returns_none_for_missing(self, app):
        with app.app_context():
            assert set_enabled(99999, True) is None


class TestCrawlLog:
    def test_creates_crawl_log(self, app, sample_data_source):
        with app.app_context():
            log = create_crawl_log(sample_data_source.id)
            assert log.status == "running"
            assert log.data_source_id == sample_data_source.id

    def test_finishes_crawl_log(self, app, sample_data_source):
        with app.app_context():
            log = create_crawl_log(sample_data_source.id)
            finish_crawl_log(
                log,
                "completed",
                message="All done",
                pages_found=10,
                pages_succeeded=8,
                pages_failed=2,
                drafts_created=5,
                average_quality_score=85.5,
            )
            assert log.status == "completed"
            assert log.message == "All done"
            assert log.pages_found == 10
            assert log.pages_succeeded == 8
            assert log.pages_failed == 2
            assert log.drafts_created == 5
            assert log.average_quality_score == 85.5
            assert log.finished_at is not None

    def test_get_crawl_logs(self, app, sample_data_source):
        with app.app_context():
            create_crawl_log(sample_data_source.id)
            logs = get_crawl_logs(sample_data_source.id)
            assert len(logs) >= 1
            assert all(isinstance(log, CrawlLog) for log in logs)

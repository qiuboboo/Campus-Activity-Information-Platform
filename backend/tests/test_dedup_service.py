"""Unit tests for dedup_service."""

from datetime import datetime

from app.services.dedup_service import (
    _normalize_location,
    _normalize_title,
    check_duplicates,
    generate_fingerprint,
    generate_source_key,
    generate_title_key,
)


class TestNormalizeTitle:
    def test_removes_punctuation(self):
        assert _normalize_title("Hello, World!") == "hello world"

    def test_normalizes_whitespace(self):
        assert _normalize_title("  多个   空格  ") == "多个 空格"

    def test_preserves_chinese_and_alphanumeric(self):
        assert _normalize_title("2026年 校园科技文化节") == "2026年 校园科技文化节"

    def test_empty_string_returns_empty(self):
        assert _normalize_title("   ") == ""


class TestNormalizeLocation:
    def test_normalizes_location(self):
        assert _normalize_location(" 大学生活动中心 ") == "大学生活动中心"

    def test_returns_none_for_empty(self):
        assert _normalize_location("") is None
        assert _normalize_location(None) is None


class TestGenerateTitleKey:
    def test_generates_consistent_hash(self):
        k1 = generate_title_key("校园科技文化节")
        k2 = generate_title_key("校园科技文化节")
        assert k1 == k2

    def test_different_titles_produce_different_keys(self):
        k1 = generate_title_key("讲座")
        k2 = generate_title_key("竞赛")
        assert k1 != k2

    def test_empty_title_returns_empty(self):
        assert generate_title_key("  ") == ""


class TestGenerateSourceKey:
    def test_generates_md5_from_url(self):
        key = generate_source_key("https://example.edu.cn/event")
        assert len(key) == 32

    def test_strips_trailing_slash(self):
        k1 = generate_source_key("https://example.edu.cn/event/")
        k2 = generate_source_key("https://example.edu.cn/event")
        assert k1 == k2

    def test_returns_none_for_no_url(self):
        assert generate_source_key(None) is None
        assert generate_source_key("") is None


class TestGenerateFingerprint:
    def test_produces_consistent_fingerprint(self):
        dt = datetime.fromisoformat("2026-05-10T19:00:00")
        f1 = generate_fingerprint("校园科技文化节", dt, "大礼堂")
        f2 = generate_fingerprint("校园科技文化节", dt, "大礼堂")
        assert f1 == f2

    def test_different_location_produces_different_fingerprint(self):
        dt = datetime.fromisoformat("2026-05-10T19:00:00")
        f1 = generate_fingerprint("讲座", dt, "大礼堂")
        f2 = generate_fingerprint("讲座", dt, "图书馆")
        assert f1 != f2

    def test_handles_none_location(self):
        dt = datetime.fromisoformat("2026-05-10T19:00:00")
        f = generate_fingerprint("讲座", dt, None)
        assert len(f) == 32

    def test_handles_none_date(self):
        f = generate_fingerprint("讲座", None, "大礼堂")
        assert len(f) == 32


class TestCheckDuplicates:
    def test_no_duplicates_for_new_poster(self, app):
        with app.app_context():
            result = check_duplicates(
                "全新活动",
                "https://example.edu.cn/new",
                None,
                None,
            )
            assert result["is_duplicate"] is False
            assert result["duplicate_group_key"] is None

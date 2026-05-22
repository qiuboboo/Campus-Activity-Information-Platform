"""Unit tests for fallback_extractor."""

from datetime import datetime

from app.services.fallback_extractor import fallback_extract


class TestFallbackExtract:
    def test_extracts_title_from_first_line(self):
        result = fallback_extract("校园科技文化节开幕式\n将于2026年5月10日在大礼堂举行")
        assert result["title"] == "校园科技文化节开幕式"

    def test_extracts_event_time_chinese_format(self):
        result = fallback_extract("活动将于2026年5月10日19:00在大礼堂举行")
        assert result["event_time"] is not None
        assert isinstance(result["event_time"], datetime)
        assert result["event_time"].year == 2026
        assert result["event_time"].month == 5
        assert result["event_time"].day == 10

    def test_extracts_event_time_iso_format(self):
        result = fallback_extract("活动日期：2026-05-10 地点：大礼堂")
        assert result["event_time"] is not None
        assert result["event_time"].month == 5

    def test_extracts_location(self):
        result = fallback_extract("在大礼堂举行科技节开幕式")
        assert result["location"] is not None
        assert "大礼堂" in result["location"]

    def test_extracts_organizer(self):
        result = fallback_extract("由校团委主办的校园科技文化节")
        assert result["organizer"] is not None
        assert "校团委" in result["organizer"]

    def test_extracts_tags(self):
        result = fallback_extract("校园科技文化节开幕式讲座将于2026年5月10日在大礼堂举行")
        assert "科技" in result["tags"]
        assert "讲座" in result["tags"]

    def test_extracts_activity_type(self):
        result = fallback_extract("科技创新讲座将于2026年5月10日举行")
        assert result["activity_type"] in ("讲座", "科技", None)

    def test_empty_input_returns_empty(self):
        result = fallback_extract("")
        assert result == {}

    def test_none_input_returns_empty(self):
        result = fallback_extract(None)
        assert result == {}

    def test_extracts_evening_time_with_12h_conversion(self):
        result = fallback_extract("活动将于2026年5月10日晚7点30分在大礼堂举行")
        assert result["event_time"] is not None
        assert result["event_time"].hour == 19
        assert result["event_time"].minute == 30

    def test_location_with_venue_suffix(self):
        result = fallback_extract("在图书馆报告厅举办")
        assert result["location"] is not None
        assert "图书馆报告厅" in result["location"]

    def test_organizer_with_org_suffix(self):
        result = fallback_extract("计算机学院学生会主办的编程竞赛")
        assert result["organizer"] is not None

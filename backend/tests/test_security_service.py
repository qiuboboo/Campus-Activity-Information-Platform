"""Unit tests for security_service."""

import pytest

from app.services.security_service import (
    SecurityError,
    _is_internal,
    _matches_any_domain,
    check_redirect_safety,
    mask_sensitive,
    sanitise_crawled_text,
    validate_target_url,
)


class TestIsInternal:
    def test_localhost_is_internal(self):
        assert _is_internal("localhost") is True

    def test_loopback_is_internal(self):
        assert _is_internal("127.0.0.1") is True

    def test_private_10_range_is_internal(self):
        assert _is_internal("10.0.0.1") is True

    def test_private_192_168_is_internal(self):
        assert _is_internal("192.168.1.1") is True

    def test_public_domain_is_not_internal(self):
        assert _is_internal("example.edu.cn") is False


class TestMatchesAnyDomain:
    def test_exact_match(self):
        assert _matches_any_domain("example.edu.cn", ["example.edu.cn"]) is True

    def test_subdomain_match(self):
        assert _matches_any_domain("news.example.edu.cn", ["example.edu.cn"]) is True

    def test_wildcard_match(self):
        assert _matches_any_domain("news.example.edu.cn", ["*.example.edu.cn"]) is True

    def test_wildcard_exact_match(self):
        assert _matches_any_domain("example.edu.cn", ["*.example.edu.cn"]) is True

    def test_no_match(self):
        assert _matches_any_domain("evil.com", ["example.edu.cn"]) is False

    def test_multiple_domains(self):
        assert _matches_any_domain("sysu.edu.cn", ["qq.com", "sysu.edu.cn", "baidu.com"]) is True

    def test_empty_allowed_list(self):
        assert _matches_any_domain("any.com", []) is False


class TestValidateTargetUrl:
    def test_allows_valid_url_with_allowed_domain(self):
        url = validate_target_url("https://example.edu.cn/events", ["example.edu.cn"])
        assert url == "https://example.edu.cn/events"

    def test_rejects_internal_ip(self):
        with pytest.raises(SecurityError):
            validate_target_url("https://127.0.0.1/admin")

    def test_rejects_localhost(self):
        with pytest.raises(SecurityError):
            validate_target_url("http://localhost:5000/secret")

    def test_rejects_non_allowed_domain(self):
        with pytest.raises(SecurityError, match="not in allowed domains"):
            validate_target_url("https://evil.com/page", ["example.edu.cn"])

    def test_rejects_disallowed_scheme(self):
        with pytest.raises(SecurityError, match="Disallowed URL scheme"):
            validate_target_url("ftp://example.edu.cn/file")

    def test_allows_url_without_domain_list(self):
        url = validate_target_url("https://sysu.edu.cn/news")
        assert url == "https://sysu.edu.cn/news"


class TestCheckRedirectSafety:
    def test_allows_same_origin_redirect(self):
        result = check_redirect_safety(
            "https://example.edu.cn/page",
            "https://example.edu.cn/detail",
        )
        assert result == "https://example.edu.cn/detail"

    def test_rejects_cross_domain_redirect(self):
        with pytest.raises(SecurityError, match="Cross-domain redirect"):
            check_redirect_safety(
                "https://example.edu.cn/page",
                "https://evil.com/phishing",
            )

    def test_returns_original_for_no_redirect(self):
        result = check_redirect_safety("https://example.edu.cn/page", None)
        assert result == "https://example.edu.cn/page"


class TestSanitiseCrawledText:
    def test_escapes_html_tags(self):
        result = sanitise_crawled_text('<script>alert("xss")</script>')
        assert "<script>" not in result

    def test_strips_control_characters(self):
        result = sanitise_crawled_text("正常文本\x00\x08")
        assert "\x00" not in result
        assert "\x08" not in result


class TestMaskSensitive:
    def test_masks_phone_numbers(self):
        text = "联系电话：13800138000"
        result = mask_sensitive(text)
        # Pattern masks as group[:3] + "****" + group[-2:] → "138****00"
        assert "13800138000" not in result

    def test_masks_id_card(self):
        text = "身份证号：440101199001011234"
        result = mask_sensitive(text)
        # ID card should be partially masked
        assert "440101199001011234" not in result

"""
Profile API (蓝图前缀 /api/me 和 /api/notifications)
用例覆盖: 收藏列表/通知列表/已读/全部已读 的 happy path + 认证
"""
import pytest


class TestFavoriteActivities:
    def test_returns_items_envelope(self, client, admin_headers):
        resp = client.get("/api/me/favorites", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json
        assert "items" in data
        assert "page" in data
        assert "total" in data

    def test_requires_auth(self, client):
        resp = client.get("/api/me/favorites")
        assert resp.status_code == 401


class TestNotifications:
    def test_returns_empty_list_initially(self, client, admin_headers):
        resp = client.get("/api/notifications", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json
        assert resp.json["total"] == 0

    def test_requires_auth(self, client):
        resp = client.get("/api/notifications")
        assert resp.status_code == 401


class TestNotificationReadAll:
    def test_read_all_succeeds_when_no_notifications(self, client, admin_headers):
        resp = client.put("/api/notifications/read-all", headers=admin_headers)
        assert resp.status_code == 200
        assert "updated" in resp.json
        assert resp.json["updated"] == 0

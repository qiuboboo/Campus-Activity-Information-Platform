"""Integration tests for subscriptions and notifications API."""

import pytest


class TestCreateSubscription:
    def test_creates_node_subscription(self, client, admin_headers, sample_published_poster):
        """Create a subscription by knowledge node."""
        # sample_published_poster has nodes from rebuild_poster_knowledge
        node_ids = [pn.node_id for pn in sample_published_poster.nodes]
        if not node_ids:
            pytest.skip("no nodes generated for sample poster")

        resp = client.post(
            "/api/subscriptions",
            json={"node_id": node_ids[0]},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "item" in data
        assert data["item"]["node_id"] == node_ids[0]

    def test_creates_keyword_subscription(self, client, admin_headers):
        resp = client.post(
            "/api/subscriptions",
            json={"keyword": "讲座"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["item"]["keyword"] == "讲座"

    def test_idempotent_duplicate(self, client, admin_headers):
        """Creating the same subscription returns existing one (200)."""
        resp1 = client.post(
            "/api/subscriptions",
            json={"keyword": "科技节"},
            headers=admin_headers,
        )
        assert resp1.status_code == 201
        resp2 = client.post(
            "/api/subscriptions",
            json={"keyword": "科技节"},
            headers=admin_headers,
        )
        assert resp2.status_code == 200

    def test_rejects_empty_body(self, client, admin_headers):
        resp = client.post("/api/subscriptions", json={}, headers=admin_headers)
        assert resp.status_code == 400

    def test_rejects_both_node_and_keyword(self, client, admin_headers):
        resp = client.post(
            "/api/subscriptions",
            json={"node_id": 1, "keyword": "讲座"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.post("/api/subscriptions", json={"keyword": "讲座"})
        assert resp.status_code == 401


class TestListSubscriptions:
    def test_returns_empty_for_new_user(self, client, admin_headers):
        resp = client.get("/api/subscriptions", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_created_subscriptions(self, client, admin_headers):
        client.post(
            "/api/subscriptions",
            json={"keyword": "讲座"},
            headers=admin_headers,
        )
        resp = client.get("/api/subscriptions", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1

    def test_requires_auth(self, client):
        resp = client.get("/api/subscriptions")
        assert resp.status_code == 401


class TestDeleteSubscription:
    def test_deletes_own_subscription(self, client, admin_headers):
        create_resp = client.post(
            "/api/subscriptions",
            json={"keyword": "讲座"},
            headers=admin_headers,
        )
        sub_id = create_resp.get_json()["item"]["id"]

        resp = client.delete(f"/api/subscriptions/{sub_id}", headers=admin_headers)
        assert resp.status_code == 200

        # Verify gone
        list_resp = client.get("/api/subscriptions", headers=admin_headers)
        assert list_resp.get_json()["total"] == 0

    def test_cannot_delete_others_subscription(self, client, admin_headers, viewer_headers):
        # Admin creates a subscription
        create_resp = client.post(
            "/api/subscriptions",
            json={"keyword": "讲座"},
            headers=admin_headers,
        )
        sub_id = create_resp.get_json()["item"]["id"]

        # Viewer tries to delete it
        resp = client.delete(f"/api/subscriptions/{sub_id}", headers=viewer_headers)
        assert resp.status_code == 403

    def test_returns_404_for_missing(self, client, admin_headers):
        resp = client.delete("/api/subscriptions/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestListNotifications:
    def test_returns_empty_for_new_user(self, client, admin_headers):
        resp = client.get("/api/subscriptions/notifications", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    def test_requires_auth(self, client):
        resp = client.get("/api/subscriptions/notifications")
        assert resp.status_code == 401


class TestMarkNotificationRead:
    def test_returns_404_for_missing_notification(self, client, admin_headers):
        resp = client.put(
            "/api/subscriptions/notifications/99999/read",
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        resp = client.put("/api/subscriptions/notifications/1/read")
        assert resp.status_code == 401


class TestMarkAllNotificationsRead:
    def test_returns_zero_when_no_notifications(self, client, admin_headers):
        resp = client.put(
            "/api/subscriptions/notifications/read-all",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["updated"] == 0

    def test_requires_auth(self, client):
        resp = client.put("/api/subscriptions/notifications/read-all")
        assert resp.status_code == 401


# =============================================================================
# Corner-case tests
# =============================================================================


class TestSubscriptionEdgeCases:
    def test_whitespace_only_keyword_rejected(self, client, admin_headers):
        r = client.post("/api/subscriptions", json={"keyword": "   "}, headers=admin_headers)
        assert r.status_code == 400

    def test_cannot_access_others_subscription(self, client, admin_headers, viewer_headers):
        client.post("/api/subscriptions", json={"keyword": "讲座"}, headers=admin_headers)
        r = client.get("/api/subscriptions", headers=viewer_headers)
        assert r.get_json()["total"] == 0

    def test_notify_method_defaults_to_platform(self, client, admin_headers):
        r = client.post("/api/subscriptions", json={"keyword": "论坛"}, headers=admin_headers)
        assert r.get_json()["item"]["notify_method"] == "platform"


class TestNotificationEdgeCases:
    def test_notification_read_is_idempotent(self, client, admin_headers, app):
        from app.extensions import db
        from app.models import Notification

        with app.app_context():
            n = Notification(user_id=1, poster_id=1, title="test", body="body", is_read=True)
            db.session.add(n)
            db.session.commit()
            nid = n.id

        r = client.put(f"/api/subscriptions/notifications/{nid}/read", headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["item"]["is_read"] is True

    def test_read_all_counts_only_unread(self, client, admin_headers, app):
        from app.extensions import db
        from app.models import Notification

        with app.app_context():
            n1 = Notification(user_id=1, poster_id=1, title="t1", body="b", is_read=False)
            n2 = Notification(user_id=1, poster_id=1, title="t2", body="b", is_read=True)
            db.session.add_all([n1, n2])
            db.session.commit()

        r = client.put("/api/subscriptions/notifications/read-all", headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["updated"] == 1

    def test_cannot_read_others_notification(self, client, admin_headers, viewer_headers, app):
        from app.extensions import db
        from app.models import Notification, User

        with app.app_context():
            other = User.query.filter_by(username="viewer").first()
            n = Notification(user_id=other.id, poster_id=1, title="t", body="b")
            db.session.add(n)
            db.session.commit()
            nid = n.id

        r = client.put(f"/api/subscriptions/notifications/{nid}/read", headers=admin_headers)
        assert r.status_code == 403

    def test_notifications_filter_by_read_status(self, client, admin_headers, app):
        from app.extensions import db
        from app.models import Notification

        with app.app_context():
            n1 = Notification(user_id=1, poster_id=1, title="unread", body="b", is_read=False)
            n2 = Notification(user_id=1, poster_id=1, title="read", body="b", is_read=True)
            db.session.add_all([n1, n2])
            db.session.commit()

        r = client.get("/api/subscriptions/notifications?is_read=true", headers=admin_headers)
        assert r.status_code == 200
        items = r.get_json()["items"]
        assert all(i["is_read"] is True for i in items)

"""Tests for notification dispatch service."""

import pytest

from app.extensions import db
from app.models import Notification, Poster, Subscription, User
from app.services.notification_service import dispatch_notifications


class TestDispatchNotifications:
    def test_no_notifications_for_draft(self, sample_poster):
        """Draft posters should not trigger any notifications."""
        notifications = dispatch_notifications(sample_poster)
        assert notifications == []

    def test_no_notifications_when_no_subscriptions(self, sample_published_poster):
        """Published poster with no matching subscriptions yields nothing."""
        # Ensure no subscriptions exist
        Subscription.query.delete()
        db.session.commit()
        notifications = dispatch_notifications(sample_published_poster)
        assert notifications == []

    def test_dispatch_by_keyword_match(self, app, admin_user, sample_published_poster):
        """Keyword subscription matching poster title should create a notification."""
        # Clean state
        Subscription.query.delete()
        Notification.query.delete()
        db.session.commit()

        sub = Subscription(
            user_id=admin_user.id,
            keyword="AI",
            notify_method="platform",
        )
        db.session.add(sub)
        db.session.commit()

        # sample_published_poster title = "AI 创新应用讲座"
        notifications = dispatch_notifications(sample_published_poster)
        assert len(notifications) >= 1
        assert all(n.user_id == admin_user.id for n in notifications)

    def test_dispatch_by_node_match(self, app, admin_user, sample_published_poster):
        """Node-based subscription should match when the poster has that node."""
        # Clean state
        Subscription.query.delete()
        Notification.query.delete()
        db.session.commit()

        node_ids = [pn.node_id for pn in sample_published_poster.nodes]
        if not node_ids:
            pytest.skip("no nodes on sample poster")

        sub = Subscription(
            user_id=admin_user.id,
            node_id=node_ids[0],
            notify_method="platform",
        )
        db.session.add(sub)
        db.session.commit()

        notifications = dispatch_notifications(sample_published_poster)
        assert len(notifications) >= 1

    def test_deduplicates_user_notifications(self, app, admin_user, sample_published_poster):
        """A user with both node and keyword matches gets only one notification."""
        # Clean state
        Subscription.query.delete()
        Notification.query.delete()
        db.session.commit()

        # Add a keyword subscription that will match
        sub_kw = Subscription(
            user_id=admin_user.id,
            keyword="AI",
            notify_method="platform",
        )
        db.session.add(sub_kw)

        # Also add a node subscription if nodes exist
        node_ids = [pn.node_id for pn in sample_published_poster.nodes]
        if node_ids:
            sub_node = Subscription(
                user_id=admin_user.id,
                node_id=node_ids[0],
                notify_method="platform",
            )
            db.session.add(sub_node)
        db.session.commit()

        notifications = dispatch_notifications(sample_published_poster)
        # Should have exactly 1 notification per unique user
        user_ids = [n.user_id for n in notifications]
        assert len(user_ids) == len(set(user_ids))

    def test_notification_body_contains_poster_info(self, app, admin_user, sample_published_poster):
        """Notifications should reference the triggering poster."""
        Subscription.query.delete()
        Notification.query.delete()
        db.session.commit()

        sub = Subscription(user_id=admin_user.id, keyword="AI", notify_method="platform")
        db.session.add(sub)
        db.session.commit()

        notifications = dispatch_notifications(sample_published_poster)
        for n in notifications:
            assert n.poster_id == sample_published_poster.id
            assert sample_published_poster.title in n.title

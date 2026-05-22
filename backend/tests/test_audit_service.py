"""Unit tests for audit_service."""

import json

from app.models import AuditLog
from app.services.audit_service import create_audit_log


class TestCreateAuditLog:
    def test_creates_log_with_all_fields(self, app):
        with app.app_context():
            log = create_audit_log(
                actor_id=1,
                action="review_approve",
                target_type="poster",
                target_id=42,
                summary="Approved poster '科技节'",
                metadata={"review_comment": "looks good"},
            )
            assert log.id is not None
            assert log.actor_id == 1
            assert log.action == "review_approve"
            assert log.target_type == "poster"
            assert log.target_id == 42
            assert log.summary == "Approved poster '科技节'"
            assert log.metadata_json is not None
            metadata = json.loads(log.metadata_json)
            assert metadata["review_comment"] == "looks good"

    def test_creates_log_with_minimal_fields(self, app):
        with app.app_context():
            log = create_audit_log(actor_id=1, action="login")
            assert log.id is not None
            assert log.actor_id == 1
            assert log.action == "login"
            assert log.target_type is None
            assert log.target_id is None
            assert log.metadata_json is None

    def test_log_is_persisted(self, app):
        with app.app_context():
            log = create_audit_log(actor_id=1, action="test_action")
            fetched = AuditLog.query.get(log.id)
            assert fetched is not None
            assert fetched.action == "test_action"

    def test_metadata_with_chinese_characters(self, app):
        with app.app_context():
            log = create_audit_log(
                actor_id=1,
                action="review",
                metadata={"reason": "内容不符合规范"},
            )
            assert "内容不符合规范" in log.metadata_json

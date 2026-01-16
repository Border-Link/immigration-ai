"""
Tests for immigration case signals.

Signals are triggered by Case create/save and should:
- Create an in-app notification on case creation
- Create notification + enqueue email task on status change
"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.django_db
class TestCaseSignals:
    def test_case_creation_triggers_notification(self, monkeypatch, case_service, payment_service, case_owner):
        from users_access.services import notification_service as notification_service_module

        create_notification = MagicMock()
        monkeypatch.setattr(notification_service_module.NotificationService, "create_notification", create_notification)

        p = payment_service.create_payment(
            user_id=str(case_owner.id),
            amount=100,
            currency="USD",
            status="pending",
            payment_provider="stripe",
            provider_transaction_id="txn_signal_001",
            plan="basic",
            changed_by=case_owner,
        )
        payment_service.update_payment(payment_id=str(p.id), status="processing", changed_by=case_owner, reason="processing")
        payment_service.update_payment(payment_id=str(p.id), status="completed", changed_by=case_owner, reason="complete")

        case = case_service.create_case(user_id=str(case_owner.id), jurisdiction="US", status="draft")
        assert case is not None

        assert create_notification.called is True
        _, kwargs = create_notification.call_args
        assert kwargs["user_id"] == str(case_owner.id)
        assert kwargs["notification_type"] == "case_status_update"
        assert kwargs["related_entity_type"] == "case"
        assert kwargs["related_entity_id"] == str(case.id)

    def test_case_status_change_triggers_notification_and_email(self, monkeypatch, case_service, paid_case_with_fact, case_owner):
        from users_access.services import notification_service as notification_service_module
        from users_access.tasks import email_tasks as email_tasks_module

        create_notification = MagicMock()
        send_email_delay = MagicMock()
        monkeypatch.setattr(notification_service_module.NotificationService, "create_notification", create_notification)
        monkeypatch.setattr(email_tasks_module.send_case_status_update_email_task, "delay", send_email_delay)

        case, _fact = paid_case_with_fact
        current = case_service.get_by_id(str(case.id))

        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            updated_by_id=str(case_owner.id),
            version=current.version,
            status="evaluated",
            reason="evaluate",
        )
        assert updated is not None
        assert error is None
        assert http_status is None

        assert create_notification.called is True
        assert send_email_delay.called is True


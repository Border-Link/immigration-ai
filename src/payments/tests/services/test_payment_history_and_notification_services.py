from unittest.mock import MagicMock

import pytest

from payments.services.payment_history_service import PaymentHistoryService
from payments.services.payment_notification_service import PaymentNotificationService


@pytest.mark.django_db
class TestPaymentHistoryService:
    def test_create_and_get_history(self, pre_case_payment_pending, payment_owner):
        entry = PaymentHistoryService.create_history_entry(
            payment=pre_case_payment_pending,
            event_type="created",
            message="created",
            new_status="pending",
            changed_by=payment_owner,
            metadata={"k": "v"},
        )
        assert entry is not None
        history = PaymentHistoryService.get_by_payment(str(pre_case_payment_pending.id))
        assert len(history) >= 1
        assert history[0].payment_id == pre_case_payment_pending.id

    def test_get_recent_history(self, pre_case_payment_pending):
        history = PaymentHistoryService.get_recent_by_payment(str(pre_case_payment_pending.id), limit=5)
        assert isinstance(history, list)


@pytest.mark.django_db
class TestPaymentNotificationService:
    def test_send_notification_for_prepayment(self, monkeypatch, pre_case_payment_pending):
        # Patch NotificationService + celery delay at the module location used by PaymentNotificationService
        monkeypatch.setattr(
            "payments.services.payment_notification_service.NotificationService.create_notification",
            MagicMock(return_value=True),
        )
        monkeypatch.setattr(
            "payments.tasks.payment_tasks.send_payment_notification_task.delay",
            MagicMock(return_value=True),
        )

        ok = PaymentNotificationService.send_notification(
            payment_id=str(pre_case_payment_pending.id),
            notification_type="status_changed",
            previous_status="pending",
            new_status="processing",
        )
        assert ok is True

    def test_send_notification_payment_not_found_returns_none(self, monkeypatch):
        monkeypatch.setattr("payments.services.payment_notification_service.PaymentSelector.get_by_id", MagicMock(return_value=None))
        ok = PaymentNotificationService.send_notification(payment_id="missing", notification_type="status_changed")
        assert ok is None


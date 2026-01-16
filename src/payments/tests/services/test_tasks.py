from unittest.mock import MagicMock

import pytest


@pytest.mark.django_db
class TestPaymentTasks:
    def test_poll_payment_status_task_not_found(self, monkeypatch):
        from payments.tasks.payment_tasks import poll_payment_status_task

        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentSelector.get_by_id", MagicMock(return_value=None))
        res = poll_payment_status_task.run("missing")
        assert res["success"] is False

    def test_poll_payment_status_task_skips_terminal_status(self, monkeypatch, pre_case_payment_completed):
        from payments.tasks.payment_tasks import poll_payment_status_task

        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentSelector.get_by_id", MagicMock(return_value=pre_case_payment_completed))
        res = poll_payment_status_task.run(str(pre_case_payment_completed.id))
        assert res["success"] is True
        assert res.get("skipped") is True

    def test_poll_payment_status_task_verification_failure(self, monkeypatch, pre_case_payment_with_txn_pending):
        from payments.tasks.payment_tasks import poll_payment_status_task

        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentSelector.get_by_id", MagicMock(return_value=pre_case_payment_with_txn_pending))
        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentService.verify_payment_status", MagicMock(return_value=None))
        res = poll_payment_status_task.run(str(pre_case_payment_with_txn_pending.id))
        assert res["success"] is False

    def test_poll_pending_payments_task_queues_subtasks(self, monkeypatch):
        from payments.tasks.payment_tasks import poll_pending_payments_task, poll_payment_status_task

        fake = MagicMock()
        fake.payment_provider = "stripe"
        fake.provider_transaction_id = "txn"
        fake.created_at = __import__("django.utils.timezone").utils.timezone.now()
        fake.id = "00000000-0000-0000-0000-000000000000"

        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentSelector.get_by_status", MagicMock(return_value=[fake]))
        monkeypatch.setattr(poll_payment_status_task, "delay", MagicMock(return_value=True))

        res = poll_pending_payments_task.run()
        assert res["total"] == 2  # pending + processing lists concatenated (both patched)

    def test_retry_failed_payments_task(self, monkeypatch):
        from payments.tasks.payment_tasks import retry_failed_payments_task

        p = MagicMock()
        p.id = "00000000-0000-0000-0000-000000000000"
        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentRetryService.get_retryable_payments", MagicMock(return_value=[p]))
        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentRetryService.retry_payment", MagicMock(return_value={"success": True}))
        res = retry_failed_payments_task.run()
        assert res["success"] == 1

    def test_send_payment_notification_task(self, monkeypatch):
        from payments.tasks.payment_tasks import send_payment_notification_task

        monkeypatch.setattr("payments.tasks.payment_tasks.PaymentNotificationService.send_notification", MagicMock(return_value=True))
        res = send_payment_notification_task.run("pid", "payment_completed", None, "completed")
        assert res["success"] is True


@pytest.mark.django_db
class TestPaymentArchivalAndEmailTasks:
    def test_archive_old_payment_history_deletes(self, monkeypatch):
        from payments.tasks.payment_archival_tasks import archive_old_payment_history

        qs = MagicMock()
        qs.count.return_value = 3
        qs.delete.return_value = (3, {})
        monkeypatch.setattr("payments.tasks.payment_archival_tasks.PaymentHistory.objects.filter", MagicMock(return_value=qs))
        res = archive_old_payment_history.run()
        assert res["archived_count"] == 3

    def test_send_payment_status_email_task_sends_email(self, monkeypatch, paid_case):
        from payments.tasks.email_tasks import send_payment_status_email_task

        _case, attached_payment = paid_case
        monkeypatch.setattr("payments.tasks.email_tasks.PaymentSelector.get_by_id", MagicMock(return_value=attached_payment))
        monkeypatch.setattr("payments.tasks.email_tasks.UserProfileSelector.get_by_user", MagicMock(side_effect=Exception("no profile")))
        send_mock = MagicMock()
        monkeypatch.setattr("payments.tasks.email_tasks.SendEmailService.send_mail", send_mock)

        send_payment_status_email_task.run(
            payment_id=str(attached_payment.id),
            notification_type="payment_completed",
            previous_status="pending",
            new_status="completed",
        )
        send_mock.assert_called()


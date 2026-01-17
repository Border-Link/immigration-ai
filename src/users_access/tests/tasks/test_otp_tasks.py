import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestOtpTasks:
    def test_send_otp_email_task_uses_correct_template_and_fallback_first_name(self):
        from users_access.tasks.otp_tasks import send_otp_email_task, OTP_TEMPLATE

        with patch("users_access.tasks.otp_tasks.SendEmailService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.send_mail.return_value = True

            result = send_otp_email_task.run("alice@example.com", None, "123456")

            assert result["status"] == "success"
            assert OTP_TEMPLATE == "user_access/otp_email.html"

            kwargs = mock_service.send_mail.call_args.kwargs
            assert kwargs["template_name"] == "user_access/otp_email.html"
            assert kwargs["recipient_list"] == ["alice@example.com"]
            assert kwargs["context"]["first_name"] == "alice"
            assert kwargs["context"]["otp"] == "123456"

    def test_send_otp_email_task_retries_when_send_mail_returns_false(self):
        from users_access.tasks.otp_tasks import send_otp_email_task

        with patch("users_access.tasks.otp_tasks.SendEmailService") as mock_service_cls, patch.object(
            send_otp_email_task,
            "retry",
            side_effect=Exception("retried"),
        ) as mock_retry:
            mock_service = mock_service_cls.return_value
            mock_service.send_mail.return_value = False

            with pytest.raises(Exception, match="retried"):
                send_otp_email_task.run("bob@example.com", "Bob", "654321")

            mock_retry.assert_called_once()


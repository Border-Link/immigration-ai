import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestRuleValidationSignals:
    @patch("data_ingestion.signals.rule_validation_signals.send_rule_validation_task_email_task")
    @patch("data_ingestion.signals.rule_validation_signals.NotificationService")
    def test_signal_sends_notification_on_created_assigned_task(
        self, mock_notification_service, mock_email_task, parsed_rule, reviewer_user
    ):
        from django.utils import timezone
        from datetime import timedelta
        from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository

        # Create while patches are active, so side-effects are observable.
        RuleValidationTaskRepository.create_validation_task(
            parsed_rule=parsed_rule,
            assigned_to=reviewer_user,
            sla_deadline=timezone.now() + timedelta(days=7),
            status="pending",
        )
        mock_notification_service.create_notification.assert_called()
        mock_email_task.delay.assert_called()


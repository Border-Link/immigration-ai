import pytest
from unittest.mock import patch, MagicMock

from data_ingestion.tasks.rule_validation_tasks import notify_pending_rule_validation_tasks_task


@pytest.mark.django_db
class TestRuleValidationTasks:
    @patch("data_ingestion.tasks.rule_validation_tasks.send_rule_validation_task_email_task")
    @patch("data_ingestion.tasks.rule_validation_tasks.NotificationService")
    @patch("data_ingestion.tasks.rule_validation_tasks.RuleValidationTaskSelector")
    def test_notify_pending_tasks_assigned(
        self, mock_selector, mock_notification_service, mock_email_task, validation_task, reviewer_user
    ):
        # Assign within test to avoid signal side-effects during fixture creation
        validation_task.assigned_to = reviewer_user
        validation_task.save(update_fields=["assigned_to"])
        qs = MagicMock()
        qs.__iter__.return_value = iter([validation_task])
        qs.count.return_value = 1
        mock_selector.get_by_status.return_value = qs

        result = notify_pending_rule_validation_tasks_task.run()
        assert result["success"] is True
        assert result["notified_count"] == 1
        mock_notification_service.create_notification.assert_called()
        mock_email_task.delay.assert_called()


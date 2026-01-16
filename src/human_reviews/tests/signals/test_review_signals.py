import pytest


@pytest.mark.django_db
class TestReviewSignals:
    def test_created_with_reviewer_sends_notification_and_assignment_email(self, monkeypatch):
        from unittest.mock import MagicMock

        from human_reviews.signals.review_signals import handle_review_changes

        notif = MagicMock(name="NotificationService.create_notification")
        monkeypatch.setattr("human_reviews.signals.review_signals.NotificationService.create_notification", notif, raising=True)

        email_delay = MagicMock(name="send_review_assignment_email_task.delay")
        monkeypatch.setattr("human_reviews.signals.review_signals.send_review_assignment_email_task.delay", email_delay, raising=True)

        reviewer = type("Reviewer", (), {"id": "r1"})()
        case = type("Case", (), {"id": "c1", "user": type("U", (), {"id": "u1"})()})()
        review = type("Review", (), {"id": "rev1", "reviewer": reviewer, "case": case, "status": "pending"})()

        handle_review_changes(sender=None, instance=review, created=True)

        notif.assert_called_once()
        email_delay.assert_called_once_with(reviewer_id="r1", review_id="rev1", case_id="c1")

    def test_created_without_reviewer_is_noop(self, monkeypatch):
        from unittest.mock import MagicMock

        from human_reviews.signals.review_signals import handle_review_changes

        notif = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.NotificationService.create_notification", notif, raising=True)
        email_delay = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.send_review_assignment_email_task.delay", email_delay, raising=True)

        case = type("Case", (), {"id": "c1", "user": type("U", (), {"id": "u1"})()})()
        review = type("Review", (), {"id": "rev1", "reviewer": None, "case": case, "status": "pending"})()

        handle_review_changes(sender=None, instance=review, created=True)
        notif.assert_not_called()
        email_delay.assert_not_called()

    def test_reviewer_changed_sends_assignment_notification_and_email(self, monkeypatch):
        from unittest.mock import MagicMock

        from human_reviews.signals.review_signals import handle_review_changes

        notif = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.NotificationService.create_notification", notif, raising=True)
        email_delay = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.send_review_assignment_email_task.delay", email_delay, raising=True)

        old_reviewer = type("Reviewer", (), {"id": "r_old"})()
        new_reviewer = type("Reviewer", (), {"id": "r_new"})()
        case = type("Case", (), {"id": "c1", "user": type("U", (), {"id": "u1"})()})()
        review = type("Review", (), {"id": "rev1", "reviewer": new_reviewer, "case": case, "status": "in_progress"})()
        review._previous_status = "pending"
        review._previous_reviewer = old_reviewer

        handle_review_changes(sender=None, instance=review, created=False)

        email_delay.assert_called_once_with(reviewer_id="r_new", review_id="rev1", case_id="c1")
        assert notif.call_count == 1

    def test_status_to_completed_sends_notifications_and_completed_email(self, monkeypatch):
        from unittest.mock import MagicMock

        from human_reviews.signals.review_signals import handle_review_changes

        notif = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.NotificationService.create_notification", notif, raising=True)
        completed_delay = MagicMock()
        monkeypatch.setattr("human_reviews.signals.review_signals.send_review_completed_email_task.delay", completed_delay, raising=True)

        reviewer = type("Reviewer", (), {"id": "r1"})()
        case_user = type("U", (), {"id": "u1"})()
        case = type("Case", (), {"id": "c1", "user": case_user})()
        review = type("Review", (), {"id": "rev1", "reviewer": reviewer, "case": case, "status": "completed"})()
        review._previous_status = "in_progress"
        review._previous_reviewer = reviewer

        handle_review_changes(sender=None, instance=review, created=False)

        # reviewer + case owner notifications
        assert notif.call_count == 2
        completed_delay.assert_called_once_with(user_id="u1", review_id="rev1", case_id="c1")


import pytest


@pytest.mark.django_db
class TestCheckReviewSLADeadlinesTask:
    def test_counts_and_sends_notifications(self, monkeypatch):
        from datetime import datetime, timedelta, timezone as dt_tz
        from unittest.mock import MagicMock

        from human_reviews.tasks.review_tasks import check_review_sla_deadlines_task

        fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt_tz.utc)
        monkeypatch.setattr("human_reviews.tasks.review_tasks.timezone.now", lambda: fixed_now, raising=True)

        notif = MagicMock(name="NotificationService.create_notification")
        monkeypatch.setattr("human_reviews.tasks.review_tasks.NotificationService.create_notification", notif, raising=True)

        class FakeQS(list):
            def count(self):
                return len(self)

        reviewer = type("Reviewer", (), {"id": "r1"})()
        case = type("Case", (), {"id": "c1"})()

        urgent_review = type(
            "Review",
            (),
            {"id": "rev1", "due_date": fixed_now + timedelta(days=2), "reviewer": reviewer, "case": case},
        )()
        approaching_review = type(
            "Review",
            (),
            {"id": "rev2", "due_date": fixed_now + timedelta(days=3), "reviewer": reviewer, "case": case},
        )()
        ignored_review = type(
            "Review",
            (),
            {"id": "rev3", "due_date": fixed_now + timedelta(days=10), "reviewer": reviewer, "case": case},
        )()
        no_due_date = type("Review", (), {"id": "rev4", "due_date": None, "reviewer": reviewer, "case": case})()
        no_reviewer = type(
            "Review",
            (),
            {"id": "rev5", "due_date": fixed_now + timedelta(days=2), "reviewer": None, "case": case},
        )()

        qs = FakeQS([urgent_review, approaching_review, ignored_review, no_due_date, no_reviewer])
        monkeypatch.setattr("human_reviews.tasks.review_tasks.ReviewSelector.get_by_status", lambda *_: qs, raising=True)

        result = check_review_sla_deadlines_task.run()

        assert result["success"] is True
        assert result["urgent_reviews"] == 2  # includes no_reviewer but still counted as urgent
        assert result["approaching_reviews"] == 1
        assert result["total_checked"] == 5

        # Notifications only for reviews that have reviewer
        # urgent_review => urgent priority, approaching_review => high priority
        priorities = [call.kwargs.get("priority") for call in notif.call_args_list]
        assert "urgent" in priorities
        assert "high" in priorities

    def test_retry_on_exception(self, monkeypatch):
        from human_reviews.tasks.review_tasks import check_review_sla_deadlines_task

        monkeypatch.setattr(
            "human_reviews.tasks.review_tasks.ReviewSelector.get_by_status",
            lambda *_: (_ for _ in ()).throw(Exception("boom")),
            raising=True,
        )

        retry_calls = {"called": False}

        def fake_retry(exc=None, countdown=None, max_retries=None):
            retry_calls["called"] = True
            retry_calls["exc"] = exc
            retry_calls["countdown"] = countdown
            retry_calls["max_retries"] = max_retries
            raise RuntimeError("retried")

        monkeypatch.setattr(check_review_sla_deadlines_task, "retry", fake_retry, raising=True)

        with pytest.raises(RuntimeError):
            check_review_sla_deadlines_task.run()

        assert retry_calls["called"] is True
        assert str(retry_calls["exc"]) == "boom"
        assert retry_calls["countdown"] == 300
        assert retry_calls["max_retries"] == 3


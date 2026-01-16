import pytest


@pytest.mark.django_db
class TestHumanReviewsMetrics:
    def test_safe_create_metric_none_class_returns_none(self):
        from human_reviews.helpers.metrics import _safe_create_metric

        assert _safe_create_metric(None, "x") is None

    def test_safe_create_metric_duplicate_registration_returns_none(self):
        from human_reviews.helpers.metrics import _safe_create_metric

        class DummyMetric:
            def __init__(self, *args, **kwargs):
                raise ValueError("Duplicated timeseries in CollectorRegistry")

        assert _safe_create_metric(DummyMetric, "metric_name", "help") is None

    def test_tracking_functions_noop_when_metrics_missing(self, monkeypatch):
        import human_reviews.helpers.metrics as m

        # Force all metric handles to None (simulates prometheus_client missing)
        for attr in (
            "review_creations_total",
            "review_assignments_total",
            "review_status_transitions_total",
            "review_completion_duration_seconds",
            "review_processing_duration_seconds",
            "decision_overrides_total",
            "decision_override_duration_seconds",
            "review_notes_created_total",
            "review_notes_per_review",
            "reviewer_workload",
            "reviews_by_status",
            "review_escalations_total",
            "review_reassignments_total",
            "review_version_conflicts_total",
        ):
            monkeypatch.setattr(m, attr, None, raising=False)

        # Should not raise
        m.track_review_creation("manual")
        m.track_review_assignment("round_robin")
        m.track_review_status_transition("pending", "in_progress")
        m.track_review_completion("completed", 1.0)
        m.track_review_processing(1.0)
        m.track_decision_override("manual", "eligible", "ineligible", 0.1)
        m.track_review_note_created("general")
        m.track_review_notes_count(2)
        m.update_reviewer_workload("rid", "in_progress", 3)
        m.update_reviews_by_status("pending", 5)
        m.track_review_escalation("complexity")
        m.track_review_reassignment("workload")
        m.track_review_version_conflict("update")

    def test_gauges_and_counters_called_when_configured(self, monkeypatch):
        import importlib
        import human_reviews.helpers.metrics as m

        # human_reviews/tests/conftest.py autouse-mocks these tracking functions to isolate side effects.
        # Reload so this test validates the real metric-wiring behavior.
        m = importlib.reload(m)

        called = {"inc": 0, "observe": 0, "set": 0}

        class _Inc:
            def inc(self):
                called["inc"] += 1

        class _Obs:
            def observe(self, *_a, **_k):
                called["observe"] += 1

        class _Set:
            def set(self, *_a, **_k):
                called["set"] += 1

        class DummyCounter:
            def labels(self, **_labels):
                return _Inc()

        class DummyHist:
            def labels(self, **_labels):
                return _Obs()

            def observe(self, *_a, **_k):
                called["observe"] += 1

        class DummyGauge:
            def labels(self, **_labels):
                return _Set()

        monkeypatch.setattr(m, "review_creations_total", DummyCounter(), raising=False)
        monkeypatch.setattr(m, "review_assignments_total", DummyCounter(), raising=False)
        monkeypatch.setattr(m, "review_status_transitions_total", DummyCounter(), raising=False)
        monkeypatch.setattr(m, "review_completion_duration_seconds", DummyHist(), raising=False)
        monkeypatch.setattr(m, "review_processing_duration_seconds", DummyHist(), raising=False)
        monkeypatch.setattr(m, "reviewer_workload", DummyGauge(), raising=False)
        monkeypatch.setattr(m, "reviews_by_status", DummyGauge(), raising=False)

        m.track_review_creation("manual")
        m.track_review_assignment("round_robin")
        m.track_review_status_transition("pending", "in_progress")
        m.track_review_completion("completed", 1.0)
        m.track_review_processing(1.0)
        m.update_reviewer_workload("rid", "in_progress", 3)
        m.update_reviews_by_status("pending", 5)

        assert called["inc"] == 3
        assert called["observe"] >= 2
        assert called["set"] == 2


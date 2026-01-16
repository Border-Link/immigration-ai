"""
Tests for compliance.helpers.metrics.

We validate that metric tracking helpers:
- don't crash when prometheus_client is absent
- call through when metric objects are present
"""

import pytest


@pytest.mark.django_db
class TestMetrics:
    def test_safe_create_metric_returns_none_on_duplicate(self):
        from compliance.helpers import metrics

        class DummyMetric:
            def __init__(self, *args, **kwargs):
                raise ValueError("duplicated")

        created = metrics._safe_create_metric(DummyMetric, "name", "help", [])
        assert created is None

    def test_track_audit_log_creation_noop_when_metrics_missing(self, monkeypatch):
        from compliance.helpers import metrics

        monkeypatch.setattr(metrics, "audit_log_entries_created_total", None)
        monkeypatch.setattr(metrics, "audit_log_creation_duration_seconds", None)
        metrics.track_audit_log_creation(level="INFO", logger_name="x", duration=0.01)

    def test_track_audit_log_creation_calls_labels_and_observe(self, monkeypatch):
        from compliance.helpers import metrics

        class DummyCounter:
            def __init__(self):
                self.calls = []

            def labels(self, **kwargs):
                self.calls.append(("labels", kwargs))
                return self

            def inc(self):
                self.calls.append(("inc", None))

        class DummyHist:
            def __init__(self):
                self.observed = []

            def observe(self, v):
                self.observed.append(v)

        c = DummyCounter()
        h = DummyHist()
        monkeypatch.setattr(metrics, "audit_log_entries_created_total", c)
        monkeypatch.setattr(metrics, "audit_log_creation_duration_seconds", h)

        metrics.track_audit_log_creation(level="WARNING", logger_name="mod", duration=0.123)
        assert ("inc", None) in c.calls
        assert h.observed == [0.123]


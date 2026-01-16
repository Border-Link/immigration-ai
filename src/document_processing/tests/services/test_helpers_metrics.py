"""
Unit tests for document_processing.helpers.metrics.

Focus: safety and determinism (no Prometheus registry collisions, no crashes when prometheus_client isn't installed).
"""

from __future__ import annotations

import types

import pytest

from document_processing.helpers import metrics as dp_metrics


@pytest.mark.django_db
class TestMetricsHelpers:
    def test_safe_create_metric_returns_none_if_metric_class_missing(self):
        assert dp_metrics._safe_create_metric(None, "name") is None

    def test_safe_create_metric_returns_none_on_duplicate_registration(self):
        class _Metric:
            def __init__(self, *_args, **_kwargs):
                raise ValueError("Duplicated timeseries in CollectorRegistry")

        assert dp_metrics._safe_create_metric(_Metric, "dup_name") is None

    def test_track_functions_noop_when_metrics_not_configured(self, monkeypatch):
        # Force all metric handles to None and ensure tracking doesn't throw.
        for attr in (
            "processing_jobs_created_total",
            "processing_jobs_completed_total",
            "processing_job_duration_seconds",
            "processing_job_retries_total",
            "processing_job_retry_duration_seconds",
            "processing_job_timeouts_total",
            "processing_jobs_by_status",
            "processing_jobs_by_priority",
            "processing_history_entries_total",
        ):
            monkeypatch.setattr(dp_metrics, attr, None, raising=False)

        dp_metrics.track_processing_job_created("ocr", 5)
        dp_metrics.track_processing_job_completed("ocr", "success", 0.5)
        dp_metrics.track_processing_job_retry("ocr", "failure", 0.2)
        dp_metrics.track_processing_job_timeout("ocr")
        dp_metrics.update_processing_jobs_by_status("pending", "ocr", 10)
        dp_metrics.update_processing_jobs_by_priority(5, 3)
        dp_metrics.track_processing_history_entry("success")

    def test_update_gauges_calls_labels_set_when_configured(self, monkeypatch):
        class _Gauge:
            def __init__(self):
                self.labels_called = []
                self.set_called = []

            def labels(self, **kwargs):
                self.labels_called.append(kwargs)
                return self

            def set(self, value):
                self.set_called.append(value)

        gauge1 = _Gauge()
        gauge2 = _Gauge()
        monkeypatch.setattr(dp_metrics, "processing_jobs_by_status", gauge1, raising=False)
        monkeypatch.setattr(dp_metrics, "processing_jobs_by_priority", gauge2, raising=False)

        dp_metrics.update_processing_jobs_by_status("pending", "ocr", 2)
        dp_metrics.update_processing_jobs_by_priority(7, 9)

        assert gauge1.labels_called == [{"status": "pending", "processing_type": "ocr"}]
        assert gauge1.set_called == [2]
        assert gauge2.labels_called == [{"priority": "7"}]
        assert gauge2.set_called == [9]


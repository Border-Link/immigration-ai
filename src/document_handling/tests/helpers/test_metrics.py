import pytest


@pytest.mark.django_db
class TestMetricsHelpers:
    def test_safe_create_metric_none_class_returns_none(self):
        from document_handling.helpers.metrics import _safe_create_metric

        assert _safe_create_metric(None, "x") is None

    def test_safe_create_metric_duplicate_registration_returns_none(self):
        from document_handling.helpers.metrics import _safe_create_metric

        class DummyMetric:
            def __init__(self, *args, **kwargs):
                raise ValueError("Duplicated timeseries in CollectorRegistry")

        assert _safe_create_metric(DummyMetric, "metric_name", "help") is None

    def test_track_functions_noop_when_metrics_missing(self, monkeypatch):
        """
        In minimal installs prometheus_client may be absent. Tracking functions
        must remain safe no-ops.
        """
        import document_handling.helpers.metrics as m

        monkeypatch.setattr(m, "document_uploads_total", None, raising=True)
        monkeypatch.setattr(m, "document_upload_duration_seconds", None, raising=True)
        monkeypatch.setattr(m, "document_upload_size_bytes", None, raising=True)
        monkeypatch.setattr(m, "ocr_operations_total", None, raising=True)
        monkeypatch.setattr(m, "ocr_duration_seconds", None, raising=True)
        monkeypatch.setattr(m, "ocr_confidence_score", None, raising=True)
        monkeypatch.setattr(m, "ocr_text_length", None, raising=True)

        # Should not raise
        m.track_document_upload(status="success", document_type="passport", duration=0.1, size_bytes=123)
        m.track_ocr_operation(backend="tesseract", status="success", duration=0.2, confidence=0.9, text_length=1000)
        m.track_document_classification(classification_type="auto", status="success", duration=0.05)
        m.track_document_validation(validation_type="llm", status="success", duration=0.05)
        m.track_document_check(check_type="ocr", status="passed", duration=0.01)
        m.track_document_requirement_match(match_status="matched")
        m.track_document_expiry_extraction(status="success")
        m.track_document_reprocessing(reason="ocr_retry", status="success", duration=0.5)
        m.track_file_storage_operation(operation="store", storage_type="local", duration=0.2)
        m.track_virus_scan(backend="clamav", status="clean", duration=0.3, threat_detected=False)

    def test_track_document_upload_calls_metric_objects(self, monkeypatch):
        import document_handling.helpers.metrics as m

        called = {"inc": 0, "observe": 0}

        class _Inc:
            def inc(self):
                called["inc"] += 1

        class _Obs:
            def observe(self, *_a, **_k):
                called["observe"] += 1

        class DummyCounter:
            def labels(self, **_labels):
                return _Inc()

        class DummyHist:
            def labels(self, **_labels):
                return _Obs()

        monkeypatch.setattr(m, "document_uploads_total", DummyCounter(), raising=True)
        monkeypatch.setattr(m, "document_upload_duration_seconds", DummyHist(), raising=True)
        monkeypatch.setattr(m, "document_upload_size_bytes", DummyHist(), raising=True)

        m.track_document_upload(status="success", document_type="passport", duration=0.1, size_bytes=123)
        assert called["inc"] == 1
        assert called["observe"] >= 2  # duration + size

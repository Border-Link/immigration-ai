import pytest


@pytest.mark.unit
class TestPIIDetector:
    def test_detect_finds_multiple_pii_types_and_is_sorted(self):
        from data_ingestion.helpers.pii_detector import PIIDetector

        text = "Email a@b.com then call +1 415-555-2671. SSN 123-45-6789."
        detections = PIIDetector.detect(text)

        assert len(detections) >= 3
        assert [d.start for d in detections] == sorted(d.start for d in detections)
        assert {d.type for d in detections} >= {"email", "phone_us", "ssn"}

        for d in detections:
            assert d.value
            assert 0 <= d.start < d.end <= len(text)
            assert 0.0 <= d.confidence <= 1.0

    def test_redact_replaces_detected_values_without_leaking_original(self):
        from data_ingestion.helpers.pii_detector import PIIDetector

        # Use a UK-format number that matches our current regex (4-3-3 grouping).
        text = "Contact: jane.doe@example.com or +44 1234 567 890"
        redacted, detections = PIIDetector.redact(text)

        assert len(detections) >= 2
        assert "jane.doe@example.com" not in redacted
        assert "+44 1234 567 890" not in redacted
        assert "[EMAIL_REDACTED]" in redacted
        assert "[PHONE_REDACTED]" in redacted

    def test_redact_with_no_detections_is_noop(self):
        from data_ingestion.helpers.pii_detector import PIIDetector

        text = "No sensitive data here."
        redacted, detections = PIIDetector.redact(text, detections=[])
        assert redacted == text
        assert detections == []

    def test_has_pii_true_false(self):
        from data_ingestion.helpers.pii_detector import PIIDetector

        assert PIIDetector.has_pii("Email me at test@example.com") is True
        assert PIIDetector.has_pii("Just normal text") is False

    def test_get_pii_summary_counts(self):
        from data_ingestion.helpers.pii_detector import PIIDetector, PIIDetection

        detections = [
            PIIDetection(type="email", value="a@b.com", start=0, end=7, confidence=0.8),
            PIIDetection(type="email", value="c@d.com", start=10, end=17, confidence=0.8),
            PIIDetection(type="ssn", value="123-45-6789", start=20, end=31, confidence=0.8),
        ]
        summary = PIIDetector.get_pii_summary(detections)
        assert summary == {"email": 2, "ssn": 1}


@pytest.mark.unit
class TestRedactPIIConvenience:
    def test_redact_pii_from_text_metadata_shape_no_pii(self):
        from data_ingestion.helpers.pii_detector import redact_pii_from_text

        text = "Clean text only."
        redacted, meta = redact_pii_from_text(text)

        assert redacted == text
        assert meta["pii_detected"] is False
        assert meta["pii_count"] == 0
        assert meta["pii_types"] == {}

    def test_redact_pii_from_text_metadata_shape_with_pii(self):
        from data_ingestion.helpers.pii_detector import redact_pii_from_text

        text = "IP 10.0.0.1, email test@example.com"
        redacted, meta = redact_pii_from_text(text)

        assert "[IP_REDACTED]" in redacted
        assert "[EMAIL_REDACTED]" in redacted
        assert meta["pii_detected"] is True
        assert meta["pii_count"] >= 2
        assert meta["redacted"] is True

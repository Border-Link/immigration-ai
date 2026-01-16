"""
Tests for VirusScanService.

We validate fail-secure behavior and major branches without requiring ClamAV/AWS.
"""

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from document_handling.services.virus_scan_service import (
    VirusScanService,
    VirusScanServiceUnavailableError,
)


@pytest.mark.django_db
class TestVirusScanService:
    def test_scan_file_backend_none_skips(self, monkeypatch):
        monkeypatch.setattr(VirusScanService, "SCAN_BACKEND", "none", raising=False)
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        is_clean, threat, err = VirusScanService.scan_file(f)
        assert is_clean is True
        assert threat is None
        assert err is None

    def test_scan_file_unknown_backend_fails(self, monkeypatch):
        monkeypatch.setattr(VirusScanService, "SCAN_BACKEND", "unknown", raising=False)
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        is_clean, threat, err = VirusScanService.scan_file(f)
        assert is_clean is False
        assert err is not None

    def test_scan_file_too_large_fail_secure_true_rejects(self, monkeypatch):
        monkeypatch.setattr(VirusScanService, "SCAN_BACKEND", "clamav", raising=False)
        monkeypatch.setattr(VirusScanService, "FAIL_SECURE", True, raising=False)
        monkeypatch.setattr(VirusScanService, "MAX_SCAN_FILE_SIZE", 1, raising=False)
        f = SimpleUploadedFile("ok.pdf", b"xx", content_type="application/pdf")
        is_clean, threat, err = VirusScanService.scan_file(f)
        assert is_clean is False
        assert err is not None

    def test_scan_file_too_large_fail_secure_false_allows(self, monkeypatch):
        monkeypatch.setattr(VirusScanService, "SCAN_BACKEND", "clamav", raising=False)
        monkeypatch.setattr(VirusScanService, "FAIL_SECURE", False, raising=False)
        monkeypatch.setattr(VirusScanService, "MAX_SCAN_FILE_SIZE", 1, raising=False)
        f = SimpleUploadedFile("ok.pdf", b"xx", content_type="application/pdf")
        is_clean, threat, err = VirusScanService.scan_file(f)
        assert is_clean is True
        assert err is None

    def test_scan_file_clamav_import_error_fail_secure_true_rejects(self, monkeypatch):
        monkeypatch.setattr(VirusScanService, "SCAN_BACKEND", "clamav", raising=False)
        monkeypatch.setattr(VirusScanService, "FAIL_SECURE", True, raising=False)

        # Ensure _scan_with_clamav raises "service unavailable"
        monkeypatch.setattr(
            VirusScanService,
            "_scan_with_clamav",
            lambda *args, **kwargs: (_ for _ in ()).throw(VirusScanServiceUnavailableError("no clamav")),
            raising=True,
        )
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        is_clean, threat, err = VirusScanService.scan_file(f)
        assert is_clean is False
        assert err is not None

    def test_get_scan_status_shape(self):
        status = VirusScanService.get_scan_status()
        assert isinstance(status, dict)
        assert "enabled" in status
        assert "backend" in status


"""
Tests for FileStorageService.

We avoid using real S3/ClamAV; integrations are mocked.
Local filesystem writes are limited to pytest tmp_path.
"""

import sys
import types
import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from document_handling.services.file_storage_service import FileStorageService


@pytest.mark.django_db
class TestFileStorageService:
    def test_validate_file_rejects_too_large(self):
        f = SimpleUploadedFile("big.pdf", b"x" * (FileStorageService.MAX_FILE_SIZE + 1), content_type="application/pdf")
        ok, err = FileStorageService.validate_file(f)
        assert ok is False
        assert "exceeds" in (err or "").lower()

    def test_validate_file_rejects_extension(self):
        f = SimpleUploadedFile("bad.exe", b"not really", content_type="application/octet-stream")
        ok, err = FileStorageService.validate_file(f)
        assert ok is False
        assert "not allowed" in (err or "").lower()

    def test_validate_file_rejects_disallowed_declared_mime(self):
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/zip")
        ok, err = FileStorageService.validate_file(f)
        assert ok is False
        assert "mime type" in (err or "").lower()

    def test_validate_file_magic_import_missing_is_defensive(self, monkeypatch):
        # Force ImportError for "magic" by ensuring it's not present and import fails.
        monkeypatch.delitem(sys.modules, "magic", raising=False)

        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        ok, err = FileStorageService.validate_file(f)
        # Should not fail just because python-magic isn't available
        assert ok is True
        assert err is None

    def test_validate_file_detected_mime_mismatch_rejected(self, monkeypatch):
        dummy_magic = types.SimpleNamespace(from_buffer=lambda *args, **kwargs: "application/zip")
        monkeypatch.setitem(sys.modules, "magic", dummy_magic)

        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        ok, err = FileStorageService.validate_file(f)
        assert ok is False
        assert "detected" in (err or "").lower()

    def test_validate_file_detected_mime_allowed(self, monkeypatch):
        dummy_magic = types.SimpleNamespace(from_buffer=lambda *args, **kwargs: "application/pdf")
        monkeypatch.setitem(sys.modules, "magic", dummy_magic)

        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        ok, err = FileStorageService.validate_file(f)
        assert ok is True
        assert err is None

    def test_generate_file_path_has_expected_prefix_and_extension(self):
        p = FileStorageService.generate_file_path("caseid", "dtype", "myfile.PDF")
        assert p.startswith("case_documents/caseid/dtype/")
        assert p.lower().endswith(".pdf")

    def test_store_file_local_writes_to_media_root(self, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")
        ok, err = FileStorageService.store_file_local(f, "case_documents/a/b/test.pdf")
        assert ok is True
        assert err is None
        assert (tmp_path / "case_documents" / "a" / "b" / "test.pdf").exists()

    def test_store_file_runs_virus_scan_and_rejects_threat(self, monkeypatch):
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")

        from document_handling.services import virus_scan_service

        monkeypatch.setattr(
            virus_scan_service.VirusScanService,
            "scan_file",
            lambda *args, **kwargs: (False, "EICAR-Test-File", None),
            raising=True,
        )
        file_path, err = FileStorageService.store_file(file=f, case_id="c", document_type_id="d")
        assert file_path is None
        assert "threat" in (err or "").lower()

    def test_store_file_scan_error_fails_secure(self, monkeypatch):
        f = SimpleUploadedFile("ok.pdf", b"%PDF-1.4\n...", content_type="application/pdf")

        from document_handling.services import virus_scan_service

        def boom(*args, **kwargs):
            raise Exception("scanner down")

        monkeypatch.setattr(virus_scan_service.VirusScanService, "scan_file", boom, raising=True)
        file_path, err = FileStorageService.store_file(file=f, case_id="c", document_type_id="d")
        assert file_path is None
        assert "virus scan error" in (err or "").lower()

    def test_get_file_url_local(self, settings):
        settings.USE_S3_STORAGE = False
        settings.MEDIA_URL = "/media/"
        url = FileStorageService.get_file_url("case_documents/a/b/test.pdf", case_id="c", user_id="u")
        assert url.endswith("/media/case_documents/a/b/test.pdf")

    def test_delete_file_local_missing_returns_false(self, settings, tmp_path):
        settings.USE_S3_STORAGE = False
        settings.MEDIA_ROOT = tmp_path
        ok = FileStorageService.delete_file("case_documents/missing.pdf")
        assert ok is False


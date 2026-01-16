"""
API tests for CallSessionSpeechAPI.
"""

import pytest
from rest_framework import status
from unittest.mock import MagicMock


BASE = "/api/v1/ai-calls"


@pytest.mark.django_db
class TestCallSessionSpeechAPI:
    def test_requires_auth(self, api_client, call_session_in_progress):
        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/speech/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_in_progress(self, api_client, call_session_ready, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/{call_session_ready.id}/speech/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_requires_audio_file(self, api_client, call_session_in_progress, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/speech/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_audio_too_large(self, api_client, call_session_in_progress, case_owner):
        from django.core.files.uploadedfile import SimpleUploadedFile

        api_client.force_authenticate(user=case_owner)
        big = b"x" * (10 * 1024 * 1024 + 1)
        audio = SimpleUploadedFile("audio.wav", big, content_type="audio/wav")
        resp = api_client.post(
            f"{BASE}/sessions/{call_session_in_progress.id}/speech/",
            data={"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_audio_validation_failure(self, api_client, call_session_in_progress, case_owner, monkeypatch):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from ai_calls.helpers import voice_utils as voice_utils_module

        api_client.force_authenticate(user=case_owner)
        monkeypatch.setattr(
            voice_utils_module,
            "validate_audio_quality",
            MagicMock(return_value=(False, "bad", None)),
        )

        audio = SimpleUploadedFile("audio.wav", b"RIFFxxxxWAVE" + b"x" * 500, content_type="audio/wav")
        resp = api_client.post(
            f"{BASE}/sessions/{call_session_in_progress.id}/speech/",
            data={"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_speech_processing_error(self, api_client, call_session_in_progress, case_owner, monkeypatch):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from ai_calls.helpers import voice_utils as voice_utils_module
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        api_client.force_authenticate(user=case_owner)
        monkeypatch.setattr(voice_utils_module, "validate_audio_quality", MagicMock(return_value=(True, None, {})))
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "process_user_speech",
            MagicMock(return_value={"error": "stt failed"}),
        )

        audio = SimpleUploadedFile("audio.wav", b"RIFFxxxxWAVE" + b"x" * 500, content_type="audio/wav")
        resp = api_client.post(
            f"{BASE}/sessions/{call_session_in_progress.id}/speech/",
            data={"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_ai_response_error(self, api_client, call_session_in_progress, case_owner, monkeypatch):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from ai_calls.helpers import voice_utils as voice_utils_module
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        api_client.force_authenticate(user=case_owner)
        monkeypatch.setattr(voice_utils_module, "validate_audio_quality", MagicMock(return_value=(True, None, {})))
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "process_user_speech",
            MagicMock(return_value={"text": "Hi", "confidence": 0.9, "turn_id": "t1"}),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "generate_ai_response",
            MagicMock(return_value={"error": "llm failed"}),
        )

        audio = SimpleUploadedFile("audio.wav", b"RIFFxxxxWAVE" + b"x" * 500, content_type="audio/wav")
        resp = api_client.post(
            f"{BASE}/sessions/{call_session_in_progress.id}/speech/",
            data={"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_success(self, api_client, call_session_in_progress, case_owner, monkeypatch):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from ai_calls.helpers import voice_utils as voice_utils_module
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        api_client.force_authenticate(user=case_owner)
        monkeypatch.setattr(voice_utils_module, "validate_audio_quality", MagicMock(return_value=(True, None, {"sample_rate": 16000})))
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "process_user_speech",
            MagicMock(return_value={"text": "Hi", "confidence": 0.9, "turn_id": "t1"}),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "generate_ai_response",
            MagicMock(return_value={"text": "Based on your case information, hello.", "turn_id": "t2", "guardrails_triggered": False}),
        )

        audio = SimpleUploadedFile("audio.wav", b"RIFFxxxxWAVE" + b"x" * 500, content_type="audio/wav")
        resp = api_client.post(
            f"{BASE}/sessions/{call_session_in_progress.id}/speech/",
            data={"audio": audio},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["text"] == "Hi"
        assert resp.data["data"]["ai_response"]["turn_id"] == "t2"


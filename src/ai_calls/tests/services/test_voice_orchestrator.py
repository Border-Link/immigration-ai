"""
Tests for VoiceOrchestrator.

All external integrations are mocked:
- STT (ExternalSpeechToTextClient)
- TTS (ExternalTextToSpeechClient)
- LLM (LLMClient)
"""

import pytest
from unittest.mock import MagicMock


@pytest.mark.django_db
class TestVoiceOrchestratorProcessUserSpeech:
    def test_process_user_speech_session_not_found(self, voice_orchestrator):
        result = voice_orchestrator.process_user_speech(b"audio", "00000000-0000-0000-0000-000000000000")
        assert "error" in result

    def test_process_user_speech_requires_in_progress(self, voice_orchestrator, call_session_ready):
        result = voice_orchestrator.process_user_speech(b"audio", str(call_session_ready.id))
        assert "error" in result

    def test_process_user_speech_success_creates_user_transcript(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        monkeypatch.setattr(
            voice_orchestrator_module,
            "normalize_audio_for_stt",
            MagicMock(name="normalize_audio_for_stt", return_value=(b"norm", None, {"sample_rate": 16000})),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_speech_to_text",
            MagicMock(name="_speech_to_text", return_value={"text": "Hello", "confidence": 0.9}),
        )

        result = voice_orchestrator.process_user_speech(b"audio", str(call_session_in_progress.id))
        assert result["text"] == "Hello"
        assert result["confidence"] == 0.9
        assert "turn_id" in result

    def test_process_user_speech_stt_error_returns_error(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from ai_calls.selectors.call_audit_log_selector import CallAuditLogSelector

        monkeypatch.setattr(
            voice_orchestrator_module,
            "normalize_audio_for_stt",
            MagicMock(name="normalize_audio_for_stt", return_value=(b"norm", None, None)),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_speech_to_text",
            MagicMock(name="_speech_to_text", return_value={"error": "stt failed"}),
        )

        result = voice_orchestrator.process_user_speech(b"audio", str(call_session_in_progress.id))
        assert "error" in result
        # Audit log should be written
        logs = CallAuditLogSelector.get_by_call_session(call_session_in_progress)
        assert logs.filter(event_type="system_error").count() >= 1

    def test_process_user_speech_empty_text_returns_error(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        monkeypatch.setattr(
            voice_orchestrator_module,
            "normalize_audio_for_stt",
            MagicMock(name="normalize_audio_for_stt", return_value=(b"norm", None, None)),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_speech_to_text",
            MagicMock(name="_speech_to_text", return_value={"text": "   ", "confidence": 0.9}),
        )

        result = voice_orchestrator.process_user_speech(b"audio", str(call_session_in_progress.id))
        assert "error" in result


@pytest.mark.django_db
class TestVoiceOrchestratorGenerateAIResponse:
    def test_generate_ai_response_session_not_found(self, voice_orchestrator):
        result = voice_orchestrator.generate_ai_response("hi", "00000000-0000-0000-0000-000000000000")
        assert "error" in result

    def test_generate_ai_response_requires_in_progress(self, voice_orchestrator, call_session_ready):
        result = voice_orchestrator.generate_ai_response("hi", str(call_session_ready.id))
        assert "error" in result

    def test_generate_ai_response_refusal_path_updates_refusals_and_logs(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from ai_calls.selectors.call_session_selector import CallSessionSelector
        from ai_calls.selectors.call_audit_log_selector import CallAuditLogSelector

        # Force guardrails refusal
        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_user_input_pre_prompt",
            MagicMock(return_value=(False, "No", "refuse", ["fraud"])),
        )

        res = voice_orchestrator.generate_ai_response("how to fake documents", str(call_session_in_progress.id))
        assert "text" in res
        assert res.get("guardrails_triggered") is True
        assert res.get("action") == "refused"

        updated = CallSessionSelector.get_by_id(str(call_session_in_progress.id))
        assert updated.refusals_count == call_session_in_progress.refusals_count + 1

        logs = CallAuditLogSelector.get_by_call_session(updated)
        assert logs.filter(event_type="refusal").count() >= 1

    def test_generate_ai_response_llm_error_returns_error_and_can_fail_session(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from ai_calls.selectors.call_session_selector import CallSessionSelector

        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_user_input_pre_prompt",
            MagicMock(return_value=(True, None, "allow", [])),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_call_llm",
            MagicMock(return_value={"error": "service unavailable"}),
        )

        res = voice_orchestrator.generate_ai_response("hi", str(call_session_in_progress.id))
        assert "error" in res

        updated = CallSessionSelector.get_by_id(str(call_session_in_progress.id))
        assert updated.status == "failed"

    def test_generate_ai_response_sanitizes_and_creates_ai_transcript(self, voice_orchestrator, call_session_in_progress, monkeypatch):
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector

        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_user_input_pre_prompt",
            MagicMock(return_value=(True, None, "allow", [])),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_call_llm",
            MagicMock(return_value={"content": "You are guaranteed approval. You must do X.", "model": "test-model"}),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_ai_response_post_response",
            MagicMock(return_value=(False, "violations", "sanitize", ["guarantee", "legal_advice", "missing_safety_language"])),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_text_to_speech",
            MagicMock(return_value={"audio_data": b"mp3", "content_type": "audio/mpeg"}),
        )

        res = voice_orchestrator.generate_ai_response("hi", str(call_session_in_progress.id), store_prompt=True)
        assert "text" in res
        assert res.get("turn_id")
        assert res.get("guardrails_triggered") is True
        assert res.get("prompt_hash") is not None

        turns = CallTranscriptSelector.get_by_call_session(call_session_in_progress)
        assert turns.filter(turn_type="ai").count() >= 1


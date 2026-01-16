"""
Focused tests for VoiceOrchestrator internals that are not covered by the higher-level
generate_ai_response/process_user_speech tests.

Goals:
- Cover _speech_to_text/_text_to_speech error handling
- Cover _call_llm success + typed error mapping
- Exercise prompt-building dependencies (voice_prompts)
"""

import pytest
from unittest.mock import MagicMock


@pytest.mark.django_db
class TestVoiceOrchestratorInternals:
    def test_speech_to_text_handles_typed_error(self, monkeypatch):
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from external_services.request.speech_client import SpeechToTextError

        fake_client = MagicMock()
        fake_client.transcribe.side_effect = SpeechToTextError("bad stt")
        monkeypatch.setattr(voice_orchestrator_module, "ExternalSpeechToTextClient", MagicMock(return_value=fake_client))

        res = VoiceOrchestrator._speech_to_text(b"audio", {"sample_rate": 16000})
        assert "error" in res
        assert res.get("error_type") == "stt_error"
        assert "original_error" in res

    def test_speech_to_text_handles_unexpected_error(self, monkeypatch):
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        fake_client = MagicMock()
        fake_client.transcribe.side_effect = Exception("boom")
        monkeypatch.setattr(voice_orchestrator_module, "ExternalSpeechToTextClient", MagicMock(return_value=fake_client))

        res = VoiceOrchestrator._speech_to_text(b"audio", {"sample_rate": 16000})
        assert "error" in res
        assert res.get("error_type") == "stt_unexpected_error"

    def test_text_to_speech_handles_typed_error(self, monkeypatch):
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module
        from external_services.request.tts_client import TextToSpeechError

        fake_client = MagicMock()
        fake_client.synthesize.side_effect = TextToSpeechError("bad tts")
        monkeypatch.setattr(voice_orchestrator_module, "ExternalTextToSpeechClient", MagicMock(return_value=fake_client))

        res = VoiceOrchestrator._text_to_speech("hello")
        assert "error" in res
        assert res.get("error_type") == "tts_error"

    def test_call_llm_success_uses_voice_system_message(self, monkeypatch, settings):
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        settings.AI_CALLS_LLM_MODEL = "test-model"

        # Build a minimal OpenAI-like response object
        usage = MagicMock(prompt_tokens=1, completion_tokens=2, total_tokens=3)
        msg = MagicMock(content="Based on your case information, ok.")
        choice = MagicMock(message=msg)
        response = MagicMock(choices=[choice], usage=usage)

        create_mock = MagicMock(return_value=response)
        fake_client = MagicMock()
        fake_client.chat.completions.create = create_mock

        fake_llm_client = MagicMock()
        fake_llm_client.client = fake_client

        monkeypatch.setattr(voice_orchestrator_module, "LLMClient", MagicMock(return_value=fake_llm_client))

        res = VoiceOrchestrator._call_llm("prompt here")
        assert res.get("content")
        assert res.get("model") == "test-model"
        assert res.get("usage", {}).get("total_tokens") == 3

        # Ensure we pass a system message (from voice_prompts) + user prompt.
        _kwargs = create_mock.call_args.kwargs
        messages = _kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "reactive-only" in messages[0]["content"].lower()
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "prompt here"

    @pytest.mark.parametrize(
        "exc_cls,expected_type",
        [
            ("LLMRateLimitError", "rate_limit"),
            ("LLMTimeoutError", "timeout"),
            ("LLMServiceUnavailableError", "service_unavailable"),
            ("LLMAPIKeyError", "api_key_error"),
            ("LLMInvalidResponseError", "invalid_response"),
        ],
    )
    def test_call_llm_maps_typed_exceptions(self, monkeypatch, exc_cls, expected_type):
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        exc = getattr(voice_orchestrator_module, exc_cls)

        fake_client = MagicMock()
        fake_client.chat.completions.create.side_effect = exc("boom")
        fake_llm_client = MagicMock(client=fake_client)

        monkeypatch.setattr(voice_orchestrator_module, "LLMClient", MagicMock(return_value=fake_llm_client))

        res = VoiceOrchestrator._call_llm("prompt")
        assert "error" in res
        assert res.get("error_type") == expected_type

    def test_generate_ai_response_includes_audio_error_when_tts_fails(self, monkeypatch, call_session_in_progress):
        """
        Even if TTS fails, we should return text + turn_id and include audio_error.
        """
        from ai_calls.services.voice_orchestrator import VoiceOrchestrator
        from ai_calls.services import voice_orchestrator as voice_orchestrator_module

        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_user_input_pre_prompt",
            MagicMock(return_value=(True, None, "allow", [])),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_call_llm",
            MagicMock(return_value={"content": "Based on your case information, ok.", "model": "test-model"}),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.GuardrailsService,
            "validate_ai_response_post_response",
            MagicMock(return_value=(True, None, "allow", [])),
        )
        monkeypatch.setattr(
            voice_orchestrator_module.VoiceOrchestrator,
            "_text_to_speech",
            MagicMock(return_value={"error": "tts failed", "error_type": "tts_error"}),
        )

        res = VoiceOrchestrator.generate_ai_response("hi", str(call_session_in_progress.id))
        assert res.get("text")
        assert res.get("turn_id")
        assert res.get("audio_error")


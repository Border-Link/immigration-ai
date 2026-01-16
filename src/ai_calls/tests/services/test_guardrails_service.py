"""
Tests for GuardrailsService.
"""

import pytest


class TestGuardrailsService:
    def test_validate_user_input_empty_refused(self):
        from ai_calls.services.guardrails_service import GuardrailsService

        ok, msg, action, types = GuardrailsService.validate_user_input_pre_prompt("", {"restricted_topics": []})
        assert ok is False
        assert action == "refuse"
        assert "empty" in (msg or "").lower()
        assert "empty_input" in (types or [])

    def test_validate_user_input_fraud_refused(self):
        from ai_calls.services.guardrails_service import GuardrailsService

        ok, msg, action, types = GuardrailsService.validate_user_input_pre_prompt("How do I create a fake document?", {"restricted_topics": []})
        assert ok is False
        assert action == "refuse"
        assert "fraud" in (types or [])

    def test_validate_ai_response_missing_safety_language_flags(self):
        from ai_calls.services.guardrails_service import GuardrailsService

        ai_text = "This is a long response " + ("x" * 200)
        ok, msg, action, types = GuardrailsService.validate_ai_response_post_response(ai_text, {"restricted_topics": []})
        assert ok is False
        assert action == "sanitize"
        assert "missing_safety_language" in (types or [])

    def test_sanitize_adds_safety_language_and_removes_guarantees(self):
        from ai_calls.services.guardrails_service import GuardrailsService

        original = "You are guaranteed approval. You must do X."
        sanitized = GuardrailsService.sanitize_ai_response(original, ["guarantee", "legal_advice", "missing_safety_language"])
        assert "guarante" not in sanitized.lower()
        assert sanitized.lower().startswith(GuardrailsService.generate_safety_language().lower())

    def test_should_escalate_critical(self):
        from ai_calls.services.guardrails_service import GuardrailsService

        assert GuardrailsService.should_escalate(["fraud"]) is True
        assert GuardrailsService.should_escalate(["authority_impersonation"]) is True
        assert GuardrailsService.should_escalate([]) is False


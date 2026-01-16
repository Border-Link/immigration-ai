"""
Unit tests for StatusTransitionValidator.
"""

import pytest

from document_processing.helpers.status_transition_validator import StatusTransitionValidator


@pytest.mark.django_db
class TestStatusTransitionValidator:
    def test_no_change_is_valid(self):
        ok, err = StatusTransitionValidator.validate_transition("pending", "pending")
        assert ok is True
        assert err is None

    def test_invalid_current_status(self):
        ok, err = StatusTransitionValidator.validate_transition("unknown", "pending")
        assert ok is False
        assert "Invalid current status" in (err or "")

    def test_invalid_new_status(self):
        ok, err = StatusTransitionValidator.validate_transition("pending", "unknown")
        assert ok is False
        assert "Invalid new status" in (err or "")

    def test_invalid_transition_includes_valid_options(self):
        ok, err = StatusTransitionValidator.validate_transition("pending", "completed")
        assert ok is False
        assert "Valid transitions" in (err or "")

    def test_valid_transitions(self):
        ok, err = StatusTransitionValidator.validate_transition("pending", "queued")
        assert ok is True
        assert err is None

    def test_get_valid_transitions(self):
        assert StatusTransitionValidator.get_valid_transitions("pending") == ["queued", "cancelled", "failed"]
        assert StatusTransitionValidator.get_valid_transitions("unknown") == []


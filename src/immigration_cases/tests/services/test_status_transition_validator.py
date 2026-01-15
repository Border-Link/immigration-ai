"""
Unit tests for immigration_cases.helpers.status_transition_validator.
"""


class TestCaseStatusTransitionValidator:
    def test_validate_transition_no_change_is_valid(self):
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        ok, error = CaseStatusTransitionValidator.validate_transition("draft", "draft")
        assert ok is True
        assert error is None

    def test_validate_transition_invalid_current_status(self):
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        ok, error = CaseStatusTransitionValidator.validate_transition("unknown", "draft")
        assert ok is False
        assert "invalid current status" in (error or "").lower()

    def test_validate_transition_invalid_new_status(self):
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        ok, error = CaseStatusTransitionValidator.validate_transition("draft", "unknown")
        assert ok is False
        assert "invalid new status" in (error or "").lower()

    def test_validate_transition_rejects_invalid_edges(self):
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        ok, error = CaseStatusTransitionValidator.validate_transition("evaluated", "draft")
        assert ok is False
        assert "invalid transition" in (error or "").lower()

    def test_validate_transition_accepts_known_edges(self):
        from immigration_cases.helpers.status_transition_validator import CaseStatusTransitionValidator

        ok, error = CaseStatusTransitionValidator.validate_transition("draft", "evaluated")
        assert ok is True
        assert error is None


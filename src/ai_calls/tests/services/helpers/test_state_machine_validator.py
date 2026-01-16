"""
Tests for call session state machine enforcement helpers.
"""


class TestCallSessionStateValidator:
    def test_validate_transition_allows_noop(self):
        from ai_calls.helpers.state_machine_validator import CallSessionStateValidator

        ok, err = CallSessionStateValidator.validate_transition("created", "created")
        assert ok is True
        assert err is None

    def test_validate_transition_valid(self):
        from ai_calls.helpers.state_machine_validator import CallSessionStateValidator

        ok, err = CallSessionStateValidator.validate_transition("created", "ready")
        assert ok is True
        assert err is None

    def test_validate_transition_rejects_unknown_statuses(self):
        from ai_calls.helpers.state_machine_validator import CallSessionStateValidator

        ok1, err1 = CallSessionStateValidator.validate_transition("nope", "ready")
        assert ok1 is False
        assert "invalid current status" in (err1 or "").lower()

        ok2, err2 = CallSessionStateValidator.validate_transition("created", "nope")
        assert ok2 is False
        assert "invalid new status" in (err2 or "").lower()

    def test_validate_transition_rejects_invalid_transition(self):
        from ai_calls.helpers.state_machine_validator import CallSessionStateValidator

        ok, err = CallSessionStateValidator.validate_transition("created", "completed")
        assert ok is False
        assert "invalid transition" in (err or "").lower()
        assert "valid transitions" in (err or "").lower()

    def test_get_valid_transitions(self):
        from ai_calls.helpers.state_machine_validator import CallSessionStateValidator

        assert "ready" in CallSessionStateValidator.get_valid_transitions("created")
        assert CallSessionStateValidator.get_valid_transitions("unknown") == []


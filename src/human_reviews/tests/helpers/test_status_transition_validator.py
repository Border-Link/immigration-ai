import pytest


@pytest.mark.django_db
class TestReviewStatusTransitionValidator:
    def test_no_change_is_valid(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        ok, err = ReviewStatusTransitionValidator.validate_transition("pending", "pending")
        assert ok is True
        assert err is None

    def test_invalid_current_status(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        ok, err = ReviewStatusTransitionValidator.validate_transition("unknown", "pending")
        assert ok is False
        assert "Invalid current status" in (err or "")

    def test_invalid_new_status(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        ok, err = ReviewStatusTransitionValidator.validate_transition("pending", "unknown")
        assert ok is False
        assert "Invalid new status" in (err or "")

    def test_invalid_transition_includes_valid_options(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        ok, err = ReviewStatusTransitionValidator.validate_transition("pending", "completed")
        assert ok is False
        assert "Valid transitions" in (err or "")

    def test_valid_transitions(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        assert ReviewStatusTransitionValidator.validate_transition("pending", "in_progress") == (True, None)
        assert ReviewStatusTransitionValidator.validate_transition("in_progress", "completed") == (True, None)
        assert ReviewStatusTransitionValidator.validate_transition("cancelled", "pending") == (True, None)

    def test_get_valid_transitions(self):
        from human_reviews.helpers.status_transition_validator import ReviewStatusTransitionValidator

        assert ReviewStatusTransitionValidator.get_valid_transitions("pending") == ["in_progress", "cancelled"]
        assert ReviewStatusTransitionValidator.get_valid_transitions("unknown") == []


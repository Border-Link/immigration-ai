import pytest

from payments.helpers.status_validator import PaymentStatusTransitionValidator


@pytest.mark.parametrize(
    "current,new,valid",
    [
        ("pending", "pending", True),
        ("pending", "processing", True),
        ("pending", "failed", True),
        ("pending", "completed", True),
        ("processing", "completed", True),
        ("processing", "failed", True),
        ("completed", "refunded", True),
        ("completed", "failed", False),
        ("refunded", "pending", False),
        ("unknown", "pending", False),
        ("pending", "unknown", False),
    ],
)
def test_validate_transition_matrix(current, new, valid):
    ok, err = PaymentStatusTransitionValidator.validate_transition(current, new)
    assert ok is valid
    if not valid:
        assert err


def test_get_valid_transitions():
    assert PaymentStatusTransitionValidator.get_valid_transitions("pending") == ["processing", "failed", "completed"]
    assert PaymentStatusTransitionValidator.get_valid_transitions("refunded") == []
    assert PaymentStatusTransitionValidator.get_valid_transitions("unknown") == []


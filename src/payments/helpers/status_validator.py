"""
Payment Status Transition Validator

Validates that payment status transitions are valid according to state machine.
"""
from typing import Tuple, Optional

# Valid payment status transitions
VALID_PAYMENT_TRANSITIONS = {
    'pending': ['processing', 'failed'],
    'processing': ['completed', 'failed'],
    'completed': ['refunded'],
    'failed': ['pending'],  # Via retry
    'refunded': [],  # Terminal state
}


class PaymentStatusTransitionValidator:
    """Validator for payment status transitions."""
    
    @staticmethod
    def validate_transition(current_status: str, new_status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a status transition.
        
        Args:
            current_status: Current status
            new_status: Proposed new status
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_status == new_status:
            return True, None  # No change is valid
        
        if current_status not in VALID_PAYMENT_TRANSITIONS:
            return False, f"Invalid current status: {current_status}"
        
        if new_status not in VALID_PAYMENT_TRANSITIONS:
            return False, f"Invalid new status: {new_status}"
        
        if new_status not in VALID_PAYMENT_TRANSITIONS[current_status]:
            return False, (
                f"Invalid transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(VALID_PAYMENT_TRANSITIONS[current_status])}"
            )
        
        return True, None
    
    @staticmethod
    def get_valid_transitions(current_status: str) -> list:
        """Get list of valid transitions from current status."""
        return VALID_PAYMENT_TRANSITIONS.get(current_status, [])

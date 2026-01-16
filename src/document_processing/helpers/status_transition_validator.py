"""
Status Transition Validator for Processing Jobs

Validates that status transitions are valid according to state machine.
"""
from typing import Tuple, Optional

# Valid status transitions
VALID_TRANSITIONS = {
    # Note: failures can occur before a job fully enters the worker pool (e.g., queueing issues,
    # validation failures), so we allow transitioning to 'failed' from 'pending'/'queued'.
    'pending': ['queued', 'cancelled', 'failed'],
    'queued': ['processing', 'cancelled', 'failed'],
    'processing': ['completed', 'failed', 'cancelled'],
    'completed': [],  # Terminal state
    'failed': ['pending'],  # Can retry
    'cancelled': []  # Terminal state
}


class StatusTransitionValidator:
    """Validator for processing job status transitions."""
    
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
        
        if current_status not in VALID_TRANSITIONS:
            return False, f"Invalid current status: {current_status}"
        
        if new_status not in VALID_TRANSITIONS:
            return False, f"Invalid new status: {new_status}"
        
        if new_status not in VALID_TRANSITIONS[current_status]:
            return False, (
                f"Invalid transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(VALID_TRANSITIONS[current_status])}"
            )
        
        return True, None
    
    @staticmethod
    def get_valid_transitions(current_status: str) -> list:
        """Get list of valid transitions from current status."""
        return VALID_TRANSITIONS.get(current_status, [])

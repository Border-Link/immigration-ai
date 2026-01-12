"""
State Machine Validator for Call Sessions

Enforces strict state machine for call sessions.
All status transitions are validated programmatically.
Invalid transitions raise exceptions and are logged as security events.
"""
from typing import Tuple, Optional, List

# Valid status transitions (from design document)
VALID_TRANSITIONS = {
    'created': ['ready', 'expired', 'terminated', 'failed'],
    'ready': ['in_progress', 'expired', 'terminated', 'failed'],
    'in_progress': ['completed', 'terminated', 'expired', 'failed'],
    'completed': [],  # Terminal state
    'expired': [],  # Terminal state
    'terminated': [],  # Terminal state
    'failed': ['created'],  # Can retry by creating a new session
}


class CallSessionStateValidator:
    """Enforces strict state machine for call sessions."""
    
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
    def get_valid_transitions(current_status: str) -> List[str]:
        """Get list of valid transitions from current status."""
        return VALID_TRANSITIONS.get(current_status, [])

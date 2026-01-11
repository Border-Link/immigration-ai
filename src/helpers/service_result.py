"""
Service Result Pattern

Helper classes for services to return results with status information
without raising exceptions that views need to catch.
"""
from typing import Optional, Any, Dict
from enum import Enum


class ServiceResultStatus(Enum):
    """Status codes for service results."""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    CONFLICT = "conflict"  # For optimistic locking conflicts
    ERROR = "error"


class ServiceResult:
    """
    Result object for service methods.
    
    Allows services to return status information without raising exceptions
    that views need to catch with try/except.
    """
    
    def __init__(
        self,
        status: ServiceResultStatus,
        data: Any = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.status = status
        self.data = data
        self.error_message = error_message
        self.error_code = error_code
    
    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.status == ServiceResultStatus.SUCCESS
    
    @property
    def is_not_found(self) -> bool:
        """Check if result is not found."""
        return self.status == ServiceResultStatus.NOT_FOUND
    
    @property
    def is_validation_error(self) -> bool:
        """Check if result is a validation error."""
        return self.status == ServiceResultStatus.VALIDATION_ERROR
    
    @property
    def is_conflict(self) -> bool:
        """Check if result is a conflict (e.g., optimistic locking)."""
        return self.status == ServiceResultStatus.CONFLICT
    
    @property
    def is_error(self) -> bool:
        """Check if result is an error."""
        return self.status == ServiceResultStatus.ERROR
    
    @classmethod
    def success(cls, data: Any = None) -> 'ServiceResult':
        """Create a success result."""
        return cls(ServiceResultStatus.SUCCESS, data=data)
    
    @classmethod
    def not_found(cls, error_message: Optional[str] = None) -> 'ServiceResult':
        """Create a not found result."""
        return cls(
            ServiceResultStatus.NOT_FOUND,
            error_message=error_message or "Resource not found"
        )
    
    @classmethod
    def validation_error(cls, error_message: str, error_code: Optional[str] = None) -> 'ServiceResult':
        """Create a validation error result."""
        return cls(
            ServiceResultStatus.VALIDATION_ERROR,
            error_message=error_message,
            error_code=error_code
        )
    
    @classmethod
    def conflict(cls, error_message: str, error_code: Optional[str] = None) -> 'ServiceResult':
        """Create a conflict result (e.g., optimistic locking)."""
        return cls(
            ServiceResultStatus.CONFLICT,
            error_message=error_message,
            error_code=error_code
        )
    
    @classmethod
    def error(cls, error_message: str, error_code: Optional[str] = None) -> 'ServiceResult':
        """Create an error result."""
        return cls(
            ServiceResultStatus.ERROR,
            error_message=error_message,
            error_code=error_code
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            'status': self.status.value,
        }
        if self.data is not None:
            result['data'] = self.data
        if self.error_message:
            result['error_message'] = self.error_message
        if self.error_code:
            result['error_code'] = self.error_code
        return result

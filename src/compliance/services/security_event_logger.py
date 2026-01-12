"""
Security Event Logger

Logs security-related events for monitoring and audit purposes.
This includes authentication failures, authorization denials, payment security events, etc.
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('django.security')


class SecurityEventLogger:
    """
    Service for logging security events.
    """
    
    @staticmethod
    def log_authentication_failure(
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log authentication failure event.
        
        Args:
            email: Email address (truncated for privacy)
            ip_address: Client IP address
            reason: Reason for failure
            metadata: Additional metadata
        """
        from main_system.utils.log_sanitizer import LogSanitizer
        
        log_data = {
            'event_type': 'authentication_failure',
            'email': LogSanitizer.truncate_email(email) if email else None,
            'ip_address': ip_address,
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
            'metadata': LogSanitizer.sanitize_dict(metadata or {})
        }
        
        logger.warning(f"Security event: {log_data}")
    
    @staticmethod
    def log_authorization_denial(
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log authorization denial event (403 Forbidden).
        
        Args:
            user_id: User ID
            resource_type: Type of resource (e.g., 'case', 'document', 'payment')
            resource_id: Resource ID
            action: Action attempted (e.g., 'read', 'update', 'delete')
            ip_address: Client IP address
            metadata: Additional metadata
        """
        from main_system.utils.log_sanitizer import LogSanitizer
        
        log_data = {
            'event_type': 'authorization_denial',
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat(),
            'metadata': LogSanitizer.sanitize_dict(metadata or {})
        }
        
        logger.warning(f"Security event: {log_data}")
    
    @staticmethod
    def log_payment_security_event(
        event_type: str,
        payment_id: Optional[str] = None,
        case_id: Optional[str] = None,
        user_id: Optional[str] = None,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log payment-related security event.
        
        Args:
            event_type: Type of event (e.g., 'amount_mismatch', 'webhook_signature_failure', 'duplicate_payment')
            payment_id: Payment ID
            case_id: Case ID
            user_id: User ID
            amount: Payment amount
            reason: Reason for the event
            metadata: Additional metadata
        """
        from main_system.utils.log_sanitizer import LogSanitizer
        
        log_data = {
            'event_type': f'payment_security_{event_type}',
            'payment_id': payment_id,
            'case_id': case_id,
            'user_id': user_id,
            'amount': amount,
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
            'metadata': LogSanitizer.sanitize_dict(metadata or {})
        }
        
        logger.warning(f"Security event: {log_data}")
    
    @staticmethod
    def log_suspicious_activity(
        activity_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log suspicious activity.
        
        Args:
            activity_type: Type of suspicious activity
            user_id: User ID
            ip_address: Client IP address
            description: Description of the activity
            metadata: Additional metadata
        """
        from main_system.utils.log_sanitizer import LogSanitizer
        
        log_data = {
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'description': description,
            'timestamp': timezone.now().isoformat(),
            'metadata': LogSanitizer.sanitize_dict(metadata or {})
        }
        
        logger.error(f"Security event: {log_data}")
    
    @staticmethod
    def log_rate_limit_exceeded(
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log rate limit exceeded event.
        
        Args:
            endpoint: API endpoint
            ip_address: Client IP address
            user_id: User ID
            metadata: Additional metadata
        """
        from main_system.utils.log_sanitizer import LogSanitizer
        
        log_data = {
            'event_type': 'rate_limit_exceeded',
            'endpoint': endpoint,
            'ip_address': ip_address,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'metadata': LogSanitizer.sanitize_dict(metadata or {})
        }
        
        logger.warning(f"Security event: {log_data}")

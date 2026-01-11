"""
Abstract Base Payment Gateway

Defines the interface that all payment gateway implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from decimal import Decimal


class BasePaymentGateway(ABC):
    """
    Abstract base class for payment gateway implementations.
    
    All payment gateway providers must implement these methods.
    """
    
    @abstractmethod
    def initialize_payment(
        self,
        amount: Decimal,
        currency: str,
        reference: str,
        customer_email: str,
        customer_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        return_url: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment with the gateway.
        
        Args:
            amount: Payment amount
            currency: Currency code (should be USD)
            reference: Unique payment reference (usually payment ID)
            customer_email: Customer email address
            customer_name: Optional customer name
            metadata: Optional metadata dictionary
            return_url: URL to redirect after payment
            callback_url: URL for webhook callbacks
            
        Returns:
            Dict with:
                - success: bool
                - payment_url: str (URL for user to complete payment)
                - transaction_id: str (gateway transaction ID)
                - reference: str (payment reference)
                - error: Optional[str] (error message if failed)
                
        Raises:
            PaymentGatewayError: For gateway-specific errors
        """
        pass
    
    @abstractmethod
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a payment status with the gateway.
        
        Args:
            transaction_id: Gateway transaction ID
            
        Returns:
            Dict with:
                - success: bool
                - status: str (pending, processing, completed, failed, refunded)
                - amount: Decimal (verified amount)
                - currency: str
                - transaction_id: str
                - reference: str (payment reference)
                - paid_at: Optional[datetime] (when payment was completed)
                - error: Optional[str] (error message if failed)
                
        Raises:
            PaymentGatewayError: For gateway-specific errors
        """
        pass
    
    @abstractmethod
    def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook event from the gateway.
        
        Args:
            payload: Webhook payload (JSON dict)
            signature: Optional webhook signature for verification
            headers: Optional HTTP headers for signature verification
            
        Returns:
            Dict with:
                - success: bool
                - event_type: str (payment.completed, payment.failed, etc.)
                - transaction_id: str
                - status: str (payment status)
                - reference: str (payment reference)
                - amount: Decimal
                - currency: str
                - verified: bool (whether signature was verified)
                - error: Optional[str] (error message if failed)
                
        Raises:
            PaymentGatewayError: For gateway-specific errors
        """
        pass
    
    @abstractmethod
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment.
        
        Args:
            transaction_id: Gateway transaction ID
            amount: Optional refund amount (partial refund if specified, full refund if None)
            reason: Optional refund reason
            
        Returns:
            Dict with:
                - success: bool
                - refund_id: str (gateway refund ID)
                - amount: Decimal (refunded amount)
                - status: str (refund status)
                - error: Optional[str] (error message if failed)
                
        Raises:
            PaymentGatewayError: For gateway-specific errors
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name (e.g., 'stripe', 'paystack').
        
        Returns:
            Provider name string
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the gateway is properly configured.
        
        Returns:
            True if configured, False otherwise
        """
        pass

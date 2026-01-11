"""
Payment Gateway Service

Orchestrates payment gateway operations and provides a unified interface
for all payment gateway providers.
"""
import logging
from typing import Dict, Optional, Any
from decimal import Decimal
from payments.gateways import BasePaymentGateway, StripeGateway, PayPalGateway, AdyenGateway
from payments.exceptions.payment_gateway_exceptions import PaymentGatewayError
from payments.models.payment import Payment

logger = logging.getLogger('django')


class PaymentGatewayService:
    """
    Service for orchestrating payment gateway operations.
    
    Provides a unified interface for all payment gateway providers.
    """
    
    # Map provider names to gateway classes
    GATEWAY_CLASSES = {
        'stripe': StripeGateway,
        'paypal': PayPalGateway,
        'adyen': AdyenGateway,
    }
    
    # Cache gateway instances
    _gateway_instances = {}
    
    @classmethod
    def get_gateway(cls, provider: str) -> Optional[BasePaymentGateway]:
        """
        Get gateway instance for a provider.
        
        Args:
            provider: Provider name ('stripe', 'paypal', 'adyen')
            
        Returns:
            Gateway instance or None if provider not found/not configured
        """
        if provider not in cls.GATEWAY_CLASSES:
            logger.error(f"Unknown payment gateway provider: {provider}")
            return None
        
        # Return cached instance if available
        if provider in cls._gateway_instances:
            gateway = cls._gateway_instances[provider]
            if gateway.is_configured():
                return gateway
        
        # Create new instance
        try:
            gateway_class = cls.GATEWAY_CLASSES[provider]
            gateway = gateway_class()
            
            if gateway.is_configured():
                cls._gateway_instances[provider] = gateway
                return gateway
            else:
                logger.warning(f"Payment gateway {provider} is not configured")
                return None
                
        except Exception as e:
            logger.error(f"Failed to initialize payment gateway {provider}: {e}", exc_info=True)
            return None
    
    @classmethod
    def initialize_payment(
        cls,
        payment: Payment,
        return_url: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment with the appropriate gateway.
        
        Args:
            payment: Payment instance
            return_url: URL to redirect after payment completion
            callback_url: URL for webhook callbacks
            
        Returns:
            Dict with payment_url, transaction_id, etc.
            
        Raises:
            PaymentGatewayError: If payment initialization fails
        """
        if not payment.payment_provider:
            raise PaymentGatewayError("Payment provider not specified")
        
        gateway = cls.get_gateway(payment.payment_provider)
        if not gateway:
            raise PaymentGatewayError(f"Payment gateway {payment.payment_provider} not available")
        
        try:
            # Get customer email from case
            customer_email = payment.case.user.email
            customer_name = None
            if hasattr(payment.case.user, 'profile'):
                profile = payment.case.user.profile
                if profile:
                    customer_name = f"{profile.first_name} {profile.last_name}".strip()
            
            # Prepare metadata
            metadata = {
                'case_id': str(payment.case.id),
                'payment_id': str(payment.id),
            }
            
            result = gateway.initialize_payment(
                amount=payment.amount,
                currency=payment.currency,
                reference=str(payment.id),
                customer_email=customer_email,
                customer_name=customer_name,
                metadata=metadata,
                return_url=return_url,
                callback_url=callback_url
            )
            
            if not result.get('success'):
                raise PaymentGatewayError(result.get('error', 'Failed to initialize payment'))
            
            return result
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize payment {payment.id}: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to initialize payment: {str(e)}")
    
    @classmethod
    def verify_payment(cls, payment: Payment) -> Dict[str, Any]:
        """
        Verify payment status with the gateway.
        
        Args:
            payment: Payment instance with provider_transaction_id
            
        Returns:
            Dict with payment status, amount, etc.
            
        Raises:
            PaymentGatewayError: If verification fails
        """
        if not payment.payment_provider:
            raise PaymentGatewayError("Payment provider not specified")
        
        if not payment.provider_transaction_id:
            raise PaymentGatewayError("Provider transaction ID not set")
        
        gateway = cls.get_gateway(payment.payment_provider)
        if not gateway:
            raise PaymentGatewayError(f"Payment gateway {payment.payment_provider} not available")
        
        try:
            result = gateway.verify_payment(payment.provider_transaction_id)
            
            if not result.get('success'):
                raise PaymentGatewayError(result.get('error', 'Failed to verify payment'))
            
            return result
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify payment {payment.id}: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to verify payment: {str(e)}")
    
    @classmethod
    def process_webhook(
        cls,
        provider: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook event from a payment gateway.
        
        Args:
            provider: Provider name ('stripe', 'paypal', 'adyen')
            payload: Webhook payload (JSON dict)
            signature: Optional webhook signature
            headers: Optional HTTP headers
            
        Returns:
            Dict with event_type, transaction_id, status, etc.
            
        Raises:
            PaymentGatewayError: If webhook processing fails
        """
        gateway = cls.get_gateway(provider)
        if not gateway:
            raise PaymentGatewayError(f"Payment gateway {provider} not available")
        
        try:
            result = gateway.process_webhook(payload, signature, headers)
            return result
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to process webhook from {provider}: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process webhook: {str(e)}")
    
    @classmethod
    def refund_payment(
        cls,
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment.
        
        Args:
            payment: Payment instance
            amount: Optional refund amount (partial refund if specified)
            reason: Optional refund reason
            
        Returns:
            Dict with refund_id, amount, status
            
        Raises:
            PaymentGatewayError: If refund fails
        """
        if not payment.payment_provider:
            raise PaymentGatewayError("Payment provider not specified")
        
        if not payment.provider_transaction_id:
            raise PaymentGatewayError("Provider transaction ID not set")
        
        if payment.status != 'completed':
            raise PaymentGatewayError("Can only refund completed payments")
        
        gateway = cls.get_gateway(payment.payment_provider)
        if not gateway:
            raise PaymentGatewayError(f"Payment gateway {payment.payment_provider} not available")
        
        try:
            result = gateway.refund_payment(
                transaction_id=payment.provider_transaction_id,
                amount=amount,
                reason=reason
            )
            
            if not result.get('success'):
                raise PaymentGatewayError(result.get('error', 'Failed to process refund'))
            
            return result
            
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Failed to refund payment {payment.id}: {e}", exc_info=True)
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get list of available (configured) payment providers.
        
        Returns:
            List of provider names that are configured
        """
        available = []
        for provider in cls.GATEWAY_CLASSES.keys():
            gateway = cls.get_gateway(provider)
            if gateway:
                available.append(provider)
        return available

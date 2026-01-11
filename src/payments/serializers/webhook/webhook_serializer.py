"""
Webhook Serializer

Serializer for webhook payload validation.
"""
from rest_framework import serializers


class WebhookPayloadSerializer(serializers.Serializer):
    """
    Serializer for webhook payload validation.
    
    Note: Webhook payloads vary by provider, so this is a minimal validation.
    Provider-specific validation happens in PaymentGatewayService.
    """
    # Common fields that most providers include
    id = serializers.CharField(required=False, allow_null=True)
    type = serializers.CharField(required=False, allow_null=True)
    event = serializers.CharField(required=False, allow_null=True)
    data = serializers.DictField(required=False, allow_null=True)
    
    class Meta:
        # Allow extra fields since webhook payloads vary by provider
        extra_kwargs = {
            'allow_extra_fields': True
        }

from django.urls import path, include
from payments.views import (
    PaymentCreateAPI,
    PaymentListAPI,
    PaymentDetailAPI,
    PaymentUpdateAPI,
    PaymentDeleteAPI,
    PaymentInitiateAPI,
    PaymentVerifyAPI,
    PaymentRefundAPI,
    PaymentHistoryAPI,
    PaymentRetryAPI,
)
from payments.views.admin import (
    PaymentAdminListAPI,
    PaymentAdminDetailAPI,
    PaymentAdminUpdateAPI,
    PaymentAdminDeleteAPI,
    BulkPaymentOperationAPI,
    PaymentStatisticsAPI,
)
from payments.views.webhooks import (
    StripeWebhookAPI,
    PayPalWebhookAPI,
    AdyenWebhookAPI,
)

app_name = 'payments'

urlpatterns = [
    # Public endpoints
    path('', PaymentListAPI.as_view(), name='payment-list'),
    path('create/', PaymentCreateAPI.as_view(), name='payment-create'),
    path('<uuid:id>/', PaymentDetailAPI.as_view(), name='payment-detail'),
    path('<uuid:id>/update/', PaymentUpdateAPI.as_view(), name='payment-update'),
    path('<uuid:id>/delete/', PaymentDeleteAPI.as_view(), name='payment-delete'),
    path('<uuid:id>/initiate/', PaymentInitiateAPI.as_view(), name='payment-initiate'),
    path('<uuid:id>/verify/', PaymentVerifyAPI.as_view(), name='payment-verify'),
    path('<uuid:id>/refund/', PaymentRefundAPI.as_view(), name='payment-refund'),
    path('<uuid:id>/history/', PaymentHistoryAPI.as_view(), name='payment-history'),
    path('<uuid:id>/retry/', PaymentRetryAPI.as_view(), name='payment-retry'),
    
    # Admin endpoints
    path('admin/', include([
        path('payments/', PaymentAdminListAPI.as_view(), name='admin-payment-list'),
        path('payments/<uuid:id>/', PaymentAdminDetailAPI.as_view(), name='admin-payment-detail'),
        path('payments/<uuid:id>/update/', PaymentAdminUpdateAPI.as_view(), name='admin-payment-update'),
        path('payments/<uuid:id>/delete/', PaymentAdminDeleteAPI.as_view(), name='admin-payment-delete'),
        path('payments/bulk-operation/', BulkPaymentOperationAPI.as_view(), name='admin-payment-bulk-operation'),
        path('statistics/', PaymentStatisticsAPI.as_view(), name='admin-payment-statistics'),
    ])),
    
    # Webhook endpoints (CSRF-exempt, called by payment gateways)
    path('webhooks/stripe/', StripeWebhookAPI.as_view(), name='stripe-webhook'),
    path('webhooks/paypal/', PayPalWebhookAPI.as_view(), name='paypal-webhook'),
    path('webhooks/adyen/', AdyenWebhookAPI.as_view(), name='adyen-webhook'),
]


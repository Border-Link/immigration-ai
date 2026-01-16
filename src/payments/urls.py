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
    PlanCaseFeePurchaseAPI,
    CaseReviewerAddonPurchaseAPI,
    CaseAiCallsAddonPurchaseAPI,
    CaseEntitlementsAPI,
)
from payments.views.admin import (
    PaymentAdminListAPI,
    PaymentAdminDetailAPI,
    PaymentAdminUpdateAPI,
    PaymentAdminDeleteAPI,
    BulkPaymentOperationAPI,
    PaymentStatisticsAPI,
    PricingItemAdminListCreateAPI,
    PricingItemAdminDetailAPI,
    PricingItemAdminUpdateAPI,
    PricingItemAdminDeleteAPI,
    PricingItemPriceAdminListUpsertAPI,
    PricingItemPriceAdminDeleteAPI,
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

    # Plan / add-on purchase endpoints (amount is derived server-side)
    path('plans/case-fee/', PlanCaseFeePurchaseAPI.as_view(), name='plan-case-fee-purchase'),
    path('cases/<uuid:case_id>/reviewer-addon/', CaseReviewerAddonPurchaseAPI.as_view(), name='case-reviewer-addon-purchase'),
    path('cases/<uuid:case_id>/ai-calls-addon/', CaseAiCallsAddonPurchaseAPI.as_view(), name='case-ai-calls-addon-purchase'),
    path('cases/<uuid:case_id>/entitlements/', CaseEntitlementsAPI.as_view(), name='case-entitlements'),
    
    # Admin endpoints
    path('admin/', include([
        path('payments/', PaymentAdminListAPI.as_view(), name='admin-payment-list'),
        path('payments/<uuid:id>/', PaymentAdminDetailAPI.as_view(), name='admin-payment-detail'),
        path('payments/<uuid:id>/update/', PaymentAdminUpdateAPI.as_view(), name='admin-payment-update'),
        path('payments/<uuid:id>/delete/', PaymentAdminDeleteAPI.as_view(), name='admin-payment-delete'),
        path('payments/bulk-operation/', BulkPaymentOperationAPI.as_view(), name='admin-payment-bulk-operation'),
        path('statistics/', PaymentStatisticsAPI.as_view(), name='admin-payment-statistics'),

        # Pricing (plans + add-ons) - API-driven admin configuration
        path('pricing/items/', PricingItemAdminListCreateAPI.as_view(), name='admin-pricing-item-list-create'),
        path('pricing/items/<uuid:id>/', PricingItemAdminDetailAPI.as_view(), name='admin-pricing-item-detail'),
        path('pricing/items/<uuid:id>/update/', PricingItemAdminUpdateAPI.as_view(), name='admin-pricing-item-update'),
        path('pricing/items/<uuid:id>/delete/', PricingItemAdminDeleteAPI.as_view(), name='admin-pricing-item-delete'),
        path('pricing/items/<uuid:id>/prices/', PricingItemPriceAdminListUpsertAPI.as_view(), name='admin-pricing-item-prices'),
        path('pricing/items/<uuid:id>/prices/<str:currency>/delete/', PricingItemPriceAdminDeleteAPI.as_view(), name='admin-pricing-item-price-delete'),
    ])),
    
    # Webhook endpoints (CSRF-exempt, called by payment gateways)
    path('webhooks/stripe/', StripeWebhookAPI.as_view(), name='stripe-webhook'),
    path('webhooks/paypal/', PayPalWebhookAPI.as_view(), name='paypal-webhook'),
    path('webhooks/adyen/', AdyenWebhookAPI.as_view(), name='adyen-webhook'),
]


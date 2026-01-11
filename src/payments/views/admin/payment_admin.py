"""
Admin API Views for Payment Management

Admin-only endpoints for managing payments.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
    BaseAdminUpdateAPI,
)
from payments.services.payment_service import PaymentService
from payments.serializers.payment.read import PaymentSerializer, PaymentListSerializer
from payments.serializers.payment.admin import (
    PaymentAdminListQuerySerializer,
    PaymentAdminUpdateSerializer,
    BulkPaymentOperationSerializer,
)
from main_system.utils.pagination import paginate_queryset


class PaymentAdminListAPI(AuthAPI):
    """
    Admin: Get list of all payments with advanced filtering.
    
    Endpoint: GET /api/v1/payments/admin/payments/
    Auth: Required (staff/superuser only)
    Query Params:
        - case_id: Filter by case ID
        - status: Filter by status
        - payment_provider: Filter by payment provider
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
        - page: Page number (default: 1)
        - page_size: Page size (default: 20, max: 100)
        
    Note: All payments are in USD (unified currency). Payment gateway handles currency conversion.
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = PaymentAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        payments = PaymentService.get_by_filters(
            case_id=str(query_serializer.validated_data.get('case_id')) if query_serializer.validated_data.get('case_id') else None,
            status=query_serializer.validated_data.get('status'),
            payment_provider=query_serializer.validated_data.get('payment_provider'),
            currency=None,  # Currency filter removed - all payments are USD
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        # Pagination
        page = query_serializer.validated_data.get('page', 1)
        page_size = query_serializer.validated_data.get('page_size', 20)
        paginated_items, pagination_metadata = paginate_queryset(payments, page=page, page_size=page_size)
        
        return self.api_response(
            message="Payments retrieved successfully.",
            data={
                'items': PaymentListSerializer(paginated_items, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class PaymentAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed payment information.
    
    Endpoint: GET /api/v1/payments/admin/payments/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Payment"
    
    def get_entity_by_id(self, entity_id):
        """Get payment by ID."""
        return PaymentService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return PaymentSerializer


class PaymentAdminUpdateAPI(BaseAdminUpdateAPI):
    """
    Admin: Update payment.
    
    Endpoint: PATCH /api/v1/payments/admin/payments/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Payment"
    
    def get_entity_by_id(self, entity_id):
        """Get payment by ID."""
        return PaymentService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the update serializer."""
        return PaymentAdminUpdateSerializer
    
    def update_entity(self, entity, validated_data):
        """Update the payment."""
        version = validated_data.pop('version', None)
        return PaymentService.update_payment(
            payment_id=str(entity.id),
            version=version,
            changed_by=self.request.user,
            reason=validated_data.get('reason'),
            **validated_data
        )
    
    def get_response_serializer_class(self):
        """Return the response serializer."""
        return PaymentSerializer


class PaymentAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete payment.
    
    Endpoint: DELETE /api/v1/payments/admin/payments/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Payment"
    
    def get_entity_by_id(self, entity_id):
        """Get payment by ID."""
        return PaymentService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the payment."""
        return PaymentService.delete_payment(
            payment_id=str(entity.id),
            changed_by=self.request.user,
            reason="Deleted by admin"
        )


class BulkPaymentOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on payments.
    
    Endpoint: POST /api/v1/payments/admin/payments/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_serializer_class(self):
        """Return the bulk payment operation serializer."""
        return BulkPaymentOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Payment"
    
    def get_entity_by_id(self, entity_id):
        """Get payment by ID."""
        return PaymentService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the payment."""
        if operation == 'delete':
            return PaymentService.delete_payment(
                payment_id=str(entity.id),
                changed_by=self.request.user,
                reason="Bulk delete operation"
            )
        elif operation == 'update_status':
            status_value = validated_data.get('status')
            return PaymentService.update_payment(
                payment_id=str(entity.id),
                changed_by=self.request.user,
                reason="Bulk status update",
                status=status_value
            )
        else:
            raise ValueError(f"Invalid operation: {operation}")

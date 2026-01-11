"""
Admin API Views for RuleParsingAuditLog Management

Admin-only endpoints for managing rule parsing audit logs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from main_system.views.admin.base import BaseAdminDetailAPI
from data_ingestion.services.audit_log_service import RuleParsingAuditLogService
from data_ingestion.serializers.audit_log.admin import (
    AuditLogAdminListQuerySerializer,
    AuditLogListSerializer,
    AuditLogDetailSerializer,
)


class RuleParsingAuditLogAdminListAPI(AuthAPI):
    """
    Admin: Get list of all rule parsing audit logs with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/audit-logs/
    Auth: Required (staff/superuser only)
    Query Params:
        - action: Filter by action type
        - status: Filter by status
        - error_type: Filter by error type
        - user_id: Filter by user ID
        - document_version_id: Filter by document version ID
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        query_serializer = AuditLogAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        logs = RuleParsingAuditLogService.get_by_filters(
            action=query_serializer.validated_data.get('action'),
            status=query_serializer.validated_data.get('status'),
            error_type=query_serializer.validated_data.get('error_type'),
            user_id=str(query_serializer.validated_data.get('user_id')) if query_serializer.validated_data.get('user_id') else None,
            document_version_id=str(query_serializer.validated_data.get('document_version_id')) if query_serializer.validated_data.get('document_version_id') else None,
            date_from=query_serializer.validated_data.get('date_from'),
            date_to=query_serializer.validated_data.get('date_to')
        )
        
        return self.api_response(
            message="Audit logs retrieved successfully.",
            data=[AuditLogListSerializer({
                'id': log.id,
                'action': log.action,
                'status': log.status,
                'error_type': log.error_type,
                'created_at': log.created_at,
            }).data for log in logs],
            status_code=status.HTTP_200_OK
        )


class RuleParsingAuditLogAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed audit log information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/audit-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Audit log"
    
    def get_entity_by_id(self, entity_id):
        """Get audit log by ID."""
        return RuleParsingAuditLogService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return AuditLogDetailSerializer
    
    def get(self, request, id):
        """Override to use custom serializer with model instance."""
        log = self.get_entity_by_id(id)
        if not log:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AuditLogDetailSerializer({
            'id': log.id,
            'document_version_id': log.document_version.id if log.document_version else None,
            'action': log.action,
            'status': log.status,
            'message': log.message,
            'error_type': log.error_type,
            'error_message': log.error_message,
            'user_id': log.user.id if log.user else None,
            'user_email': log.user.email if log.user else None,
            'metadata': log.metadata,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'created_at': log.created_at,
        })
        
        return self.api_response(
            message=f"{self.get_entity_name()} retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

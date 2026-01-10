"""
Admin API Views for RuleParsingAuditLog Management

Admin-only endpoints for managing rule parsing audit logs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.audit_log_service import RuleParsingAuditLogService
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class AuditLogSerializer:
    """Simple serializer for audit log data."""
    @staticmethod
    def to_dict(audit_log):
        return {
            'id': str(audit_log.id),
            'document_version_id': str(audit_log.document_version.id) if audit_log.document_version else None,
            'action': audit_log.action,
            'status': audit_log.status,
            'message': audit_log.message,
            'error_type': audit_log.error_type,
            'error_message': audit_log.error_message,
            'user_id': str(audit_log.user.id) if audit_log.user else None,
            'user_email': audit_log.user.email if audit_log.user else None,
            'metadata': audit_log.metadata,
            'ip_address': str(audit_log.ip_address) if audit_log.ip_address else None,
            'user_agent': audit_log.user_agent,
            'created_at': audit_log.created_at.isoformat() if audit_log.created_at else None,
        }


class AuditLogListSerializer:
    """Simple serializer for audit log list."""
    @staticmethod
    def to_dict(audit_log):
        return {
            'id': str(audit_log.id),
            'action': audit_log.action,
            'status': audit_log.status,
            'error_type': audit_log.error_type,
            'created_at': audit_log.created_at.isoformat() if audit_log.created_at else None,
        }


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
        action = request.query_params.get('action', None)
        status_filter = request.query_params.get('status', None)
        error_type = request.query_params.get('error_type', None)
        user_id = request.query_params.get('user_id', None)
        document_version_id = request.query_params.get('document_version_id', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Use service method with filters
            logs = RuleParsingAuditLogService.get_by_filters(
                action=action,
                status=status_filter,
                error_type=error_type,
                user_id=user_id,
                document_version_id=document_version_id,
                date_from=parsed_date_from,
                date_to=parsed_date_to
            )
            
            return self.api_response(
                message="Audit logs retrieved successfully.",
                data=[AuditLogListSerializer.to_dict(log) for log in logs],
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving audit logs.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RuleParsingAuditLogAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed audit log information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/audit-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            log = RuleParsingAuditLogService.get_by_id(id)
            if not log:
                return self.api_response(
                    message=f"Audit log with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Audit log retrieved successfully.",
                data=AuditLogSerializer.to_dict(log),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving audit log {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving audit log.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

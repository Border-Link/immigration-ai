"""
Admin API Views for AuditLog Management

Admin-only endpoints for managing audit logs.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from compliance.services.audit_log_service import AuditLogService
from compliance.serializers.audit_log.admin import (
    AuditLogAdminListSerializer,
    AuditLogAdminDetailSerializer,
    BulkAuditLogOperationSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class AuditLogAdminListAPI(AuthAPI):
    """
    Admin: Get list of all audit logs with advanced filtering.
    
    Endpoint: GET /api/v1/compliance/admin/audit-logs/
    Auth: Required (staff/superuser only)
    Query Params:
        - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - logger_name: Filter by logger name
        - date_from: Filter by timestamp (from)
        - date_to: Filter by timestamp (to)
        - limit: Limit number of results (default: 100)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        level = request.query_params.get('level', None)
        logger_name = request.query_params.get('logger_name', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        limit = request.query_params.get('limit', None)
        
        try:
            # Parse dates
            parsed_date_from = parse_datetime(date_from) if date_from else None
            parsed_date_to = parse_datetime(date_to) if date_to else None
            
            # Parse limit
            parsed_limit = None
            if limit:
                try:
                    parsed_limit = int(limit)
                except (ValueError, TypeError):
                    parsed_limit = None
            
            # Use service method with filters
            logs = AuditLogService.get_by_filters(
                level=level,
                logger_name=logger_name,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                limit=parsed_limit
            )
            
            return self.api_response(
                message="Audit logs retrieved successfully.",
                data=AuditLogAdminListSerializer(logs, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving audit logs.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuditLogAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed audit log information.
    
    Endpoint: GET /api/v1/compliance/admin/audit-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            log = AuditLogService.get_by_id(id)
            if not log:
                return self.api_response(
                    message=f"Audit log with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Audit log retrieved successfully.",
                data=AuditLogAdminDetailSerializer(log).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving audit log {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving audit log.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuditLogAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete an audit log.
    
    Endpoint: DELETE /api/v1/compliance/admin/audit-logs/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            success = AuditLogService.delete_audit_log(id)
            if not success:
                return self.api_response(
                    message=f"Audit log with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Audit log deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting audit log {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting audit log.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkAuditLogOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on audit logs.
    
    Endpoint: POST /api/v1/compliance/admin/audit-logs/bulk-operation/
    Auth: Required (staff/superuser only)
    Body:
        {
            "log_ids": ["uuid1", "uuid2", ...],
            "operation": "delete"
        }
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkAuditLogOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.api_response(
                message="Invalid request data.",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        log_ids = serializer.validated_data['log_ids']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'delete':
                deleted_count = 0
                failed_count = 0
                
                for log_id in log_ids:
                    success = AuditLogService.delete_audit_log(str(log_id))
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                
                return self.api_response(
                    message=f"Bulk operation completed. Deleted: {deleted_count}, Failed: {failed_count}.",
                    data={
                        'deleted_count': deleted_count,
                        'failed_count': failed_count,
                        'total_requested': len(log_ids),
                    },
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message=f"Unknown operation: {operation}",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error performing bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from compliance.services.audit_log_service import AuditLogService
from compliance.serializers.audit_log.read import (
    AuditLogListQuerySerializer,
    AuditLogSerializer,
    AuditLogListSerializer
)
from compliance.helpers.pagination import paginate_queryset
from compliance.models.audit_log import AuditLog


class AuditLogListAPI(AuthAPI):
    """Get all audit logs with filtering and pagination."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        # Validate query parameters
        query_serializer = AuditLogListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        level = validated_params.get('level')
        logger_name = validated_params.get('logger_name')
        date_from = validated_params.get('date_from')
        date_to = validated_params.get('date_to')
        limit = validated_params.get('limit', 100)
        
        # Start with base queryset based on primary filter
        if date_from or date_to:
            # Use date range filtering (highest priority)
            if not date_from:
                # If only date_to provided, get all logs up to date_to
                from django.utils import timezone
                date_from = timezone.now().replace(year=1970, month=1, day=1)  # Very early date
            if not date_to:
                # If only date_from provided, get all logs from date_from
                from django.utils import timezone
                date_to = timezone.now()
            audit_logs = AuditLogService.get_by_date_range(date_from, date_to)
        elif level:
            audit_logs = AuditLogService.get_by_level(level)
        elif logger_name:
            audit_logs = AuditLogService.get_by_logger_name(logger_name)
        else:
            audit_logs = AuditLogService.get_recent(limit)
        
        # Apply additional filters on top of base queryset
        if level and (date_from or date_to):
            # Apply level filter on date range results
            audit_logs = audit_logs.filter(level=level)
        if logger_name and (date_from or date_to or level):
            # Apply logger_name filter if not already the primary filter
            audit_logs = audit_logs.filter(logger_name=logger_name)
        
        # Paginate results
        page = validated_params.get('page', 1)
        page_size = validated_params.get('page_size', 20)
        paginated_logs, pagination_metadata = paginate_queryset(audit_logs, page=page, page_size=page_size)

        return self.api_response(
            message="Audit logs retrieved successfully.",
            data={
                'items': AuditLogListSerializer(paginated_logs, many=True).data,
                'pagination': pagination_metadata
            },
            status_code=status.HTTP_200_OK
        )


class AuditLogDetailAPI(AuthAPI):
    """Get audit log by ID."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request, id):
        audit_log = AuditLogService.get_by_id(id)
        
        if not audit_log:
            return self.api_response(
                message=f"Audit log with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        return self.api_response(
            message="Audit log retrieved successfully.",
            data=AuditLogSerializer(audit_log).data,
            status_code=status.HTTP_200_OK
        )


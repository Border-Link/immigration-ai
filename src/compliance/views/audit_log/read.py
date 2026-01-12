from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.base import BaseAdminDetailAPI
from compliance.services.audit_log_service import AuditLogService
from compliance.serializers.audit_log.read import (
    AuditLogListQuerySerializer,
    AuditLogSerializer,
    AuditLogListSerializer
)
from main_system.utils import paginate_queryset


class AuditLogListAPI(AuthAPI):
    """Get all audit logs with filtering and pagination."""
    permission_classes = [AdminPermission]

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


class AuditLogDetailAPI(BaseAdminDetailAPI):
    """Get audit log by ID."""
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Audit log"
    
    def get_entity_by_id(self, entity_id):
        """Get audit log by ID."""
        return AuditLogService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return AuditLogSerializer


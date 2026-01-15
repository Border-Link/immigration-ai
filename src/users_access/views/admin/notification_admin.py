"""
Admin API Views for Notification Management

Admin-only endpoints for managing notifications.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.base import BaseAdminDeleteAPI
from users_access.services.notification_service import NotificationService
from users_access.serializers.notification.read import NotificationSerializer, NotificationListSerializer
from users_access.serializers.notification.admin import (
    NotificationCreateSerializer,
    BulkNotificationCreateSerializer,
)
from users_access.serializers.users.admin import NotificationAdminListQuerySerializer


class NotificationAdminListAPI(AuthAPI):
    """
    Admin: Get list of all notifications with advanced filtering.
    
    Endpoint: GET /api/v1/auth/admin/notifications/
    Auth: Required (staff/superuser only)
    Query Params:
        - user_id: Filter by user ID
        - notification_type: Filter by notification type
        - priority: Filter by priority
        - is_read: Filter by read status
        - date_from: Filter by created date (from)
        - date_to: Filter by created date (to)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = NotificationAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_params = query_serializer.validated_data
        
        # Get notifications
        if validated_params.get('user_id'):
            notifications = NotificationService.get_by_user(str(validated_params.get('user_id')))
        else:
            notifications = NotificationService.get_all()
        
        # Apply filters
        if validated_params.get('notification_type'):
            notifications = notifications.filter(notification_type=validated_params.get('notification_type'))
        if validated_params.get('priority'):
            notifications = notifications.filter(priority=validated_params.get('priority'))
        if validated_params.get('is_read') is not None:
            notifications = notifications.filter(is_read=validated_params.get('is_read'))
        if validated_params.get('date_from'):
            notifications = notifications.filter(created_at__gte=validated_params.get('date_from'))
        if validated_params.get('date_to'):
            notifications = notifications.filter(created_at__lte=validated_params.get('date_to'))
        
        return self.api_response(
            message="Notifications retrieved successfully.",
            data=NotificationListSerializer(notifications, many=True).data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request):
        """
        Compatibility: tests POST `/api/admin/notifications/` to create (not `/create/`).
        """
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification = NotificationService.create_notification(
            user_id=str(serializer.validated_data['user_id']),
            notification_type=serializer.validated_data['notification_type'],
            title=serializer.validated_data['title'],
            message=serializer.validated_data['message'],
            priority=serializer.validated_data.get('priority', 'medium'),
            related_entity_type=serializer.validated_data.get('related_entity_type'),
            related_entity_id=str(serializer.validated_data['related_entity_id']) if serializer.validated_data.get('related_entity_id') else None,
            metadata=serializer.validated_data.get('metadata')
        )
        
        if notification:
            return self.api_response(
                message="Notification created successfully.",
                data=NotificationSerializer(notification).data,
                status_code=status.HTTP_201_CREATED
            )
        
        return self.api_response(
            message="Error creating notification.",
            data=None,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class NotificationAdminCreateAPI(AuthAPI):
    """
    Admin: Create a notification for a user.
    
    Endpoint: POST /api/v1/auth/admin/notifications/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification = NotificationService.create_notification(
            user_id=str(serializer.validated_data['user_id']),
            notification_type=serializer.validated_data['notification_type'],
            title=serializer.validated_data['title'],
            message=serializer.validated_data['message'],
            priority=serializer.validated_data.get('priority', 'medium'),
            related_entity_type=serializer.validated_data.get('related_entity_type'),
            related_entity_id=str(serializer.validated_data['related_entity_id']) if serializer.validated_data.get('related_entity_id') else None,
            metadata=serializer.validated_data.get('metadata')
        )
        
        if notification:
            return self.api_response(
                message="Notification created successfully.",
                data=NotificationSerializer(notification).data,
                status_code=status.HTTP_201_CREATED
            )
        else:
            return self.api_response(
                message="Error creating notification.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationAdminBulkCreateAPI(AuthAPI):
    """
    Admin: Create notifications for multiple users (bulk).
    
    Endpoint: POST /api/v1/auth/admin/notifications/bulk/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def post(self, request):
        serializer = BulkNotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        results = {
            'success': [],
            'failed': []
        }
        
        for user_id in user_ids:
            notification = NotificationService.create_notification(
                user_id=str(user_id),
                notification_type=serializer.validated_data['notification_type'],
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                priority=serializer.validated_data.get('priority', 'medium'),
                related_entity_type=serializer.validated_data.get('related_entity_type'),
                related_entity_id=str(serializer.validated_data['related_entity_id']) if serializer.validated_data.get('related_entity_id') else None,
                metadata=serializer.validated_data.get('metadata')
            )
            
            if notification:
                results['success'].append(str(user_id))
            else:
                results['failed'].append({
                    'user_id': str(user_id),
                    'error': 'Failed to create notification'
                })
        
        return self.api_response(
            message=f"Bulk notification creation completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
            data=results,
            status_code=status.HTTP_200_OK
        )


class NotificationAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete a notification.
    
    Endpoint: DELETE /api/v1/auth/admin/notifications/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Notification"
    
    def get_entity_by_id(self, entity_id):
        """Get notification by ID."""
        return NotificationService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the notification."""
        return NotificationService.delete_notification(str(entity.id))

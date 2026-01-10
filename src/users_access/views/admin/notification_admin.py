"""
Admin API Views for Notification Management

Admin-only endpoints for managing notifications.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from users_access.services.notification_service import NotificationService
from users_access.serializers.notification.read import NotificationSerializer, NotificationListSerializer
from users_access.serializers.notification.admin import (
    NotificationCreateSerializer,
    BulkNotificationCreateSerializer,
)
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


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
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        user_id = request.query_params.get('user_id', None)
        notification_type = request.query_params.get('notification_type', None)
        priority = request.query_params.get('priority', None)
        is_read = request.query_params.get('is_read', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        try:
            # Parse parameters
            is_read_bool = is_read.lower() == 'true' if is_read is not None else None
            parsed_date_from = parse_datetime(date_from) if date_from and isinstance(date_from, str) else date_from
            parsed_date_to = parse_datetime(date_to) if date_to and isinstance(date_to, str) else date_to
            
            # Get notifications
            if user_id:
                notifications = NotificationService.get_by_user(str(user_id))
            else:
                notifications = NotificationService.get_all()
            
            # Apply filters
            if notification_type:
                notifications = notifications.filter(notification_type=notification_type)
            if priority:
                notifications = notifications.filter(priority=priority)
            if is_read_bool is not None:
                notifications = notifications.filter(is_read=is_read_bool)
            if parsed_date_from:
                notifications = notifications.filter(created_at__gte=parsed_date_from)
            if parsed_date_to:
                notifications = notifications.filter(created_at__lte=parsed_date_to)
            
            return self.api_response(
                message="Notifications retrieved successfully.",
                data=NotificationListSerializer(notifications, many=True).data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving notifications: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving notifications.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationAdminCreateAPI(AuthAPI):
    """
    Admin: Create a notification for a user.
    
    Endpoint: POST /api/v1/auth/admin/notifications/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
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
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            return self.api_response(
                message="Error creating notification.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationAdminBulkCreateAPI(AuthAPI):
    """
    Admin: Create notifications for multiple users (bulk).
    
    Endpoint: POST /api/v1/auth/admin/notifications/bulk/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkNotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for user_id in user_ids:
                try:
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
                except Exception as e:
                    results['failed'].append({
                        'user_id': str(user_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk notification creation completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk notification creation: {e}", exc_info=True)
            return self.api_response(
                message="Error creating bulk notifications.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete a notification.
    
    Endpoint: DELETE /api/v1/auth/admin/notifications/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            notification = NotificationService.get_by_id(id)
            if not notification:
                return self.api_response(
                    message=f"Notification with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            deleted = NotificationService.delete_notification(id)
            if not deleted:
                return self.api_response(
                    message=f"Notification with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Notification deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting notification {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting notification.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.notification_service import NotificationService
from users_access.serializers.notification.read import NotificationSerializer, NotificationListSerializer


class NotificationListAPI(AuthAPI):
    """Get list of notifications for the current user."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        
        if unread_only:
            notifications = NotificationService.get_unread_by_user(str(request.user.id))
        else:
            notifications = NotificationService.get_by_user(str(request.user.id))

        return self.api_response(
            message="Notifications retrieved successfully.",
            data=NotificationListSerializer(notifications, many=True).data,
            status_code=status.HTTP_200_OK
        )


class NotificationDetailAPI(AuthAPI):
    """Get notification by ID."""
    permission_classes = [AuthenticationPermission]

    def get(self, request, id):
        notification = NotificationService.get_by_id(id)
        if not notification:
            return self.api_response(
                message=f"Notification with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Ensure user can only access their own notifications
        if str(notification.user.id) != str(request.user.id):
            return self.api_response(
                message="You do not have permission to access this notification.",
                data=None,
                status_code=status.HTTP_403_FORBIDDEN
            )

        return self.api_response(
            message="Notification retrieved successfully.",
            data=NotificationSerializer(notification).data,
            status_code=status.HTTP_200_OK
        )


class NotificationUnreadCountAPI(AuthAPI):
    """Get count of unread notifications for the current user."""
    permission_classes = [AuthenticationPermission]

    def get(self, request):
        count = NotificationService.count_unread(str(request.user.id))
        return self.api_response(
            message="Unread notification count retrieved successfully.",
            data={'unread_count': count},
            status_code=status.HTTP_200_OK
        )


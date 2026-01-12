from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.authentication_permission import AuthenticationPermission
from users_access.services.notification_service import NotificationService
from users_access.serializers.notification.create import NotificationMarkReadSerializer
from users_access.serializers.notification.read import NotificationSerializer


class NotificationMarkReadAPI(AuthAPI):
    """Mark a notification or all notifications as read."""
    permission_classes = [AuthenticationPermission]

    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data.get('mark_all'):
            # Mark all notifications as read
            success = NotificationService.mark_all_as_read(str(request.user.id))
            if success:
                return self.api_response(
                    message="All notifications marked as read.",
                    data=None,
                    status_code=status.HTTP_200_OK
                )
            else:
                return self.api_response(
                    message="Error marking notifications as read.",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Mark single notification as read
            notification_id = serializer.validated_data.get('notification_id')
            notification = NotificationService.mark_as_read(notification_id)
            
            if not notification:
                return self.api_response(
                    message=f"Notification with ID '{notification_id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Ensure user can only mark their own notifications as read
            if str(notification.user.id) != str(request.user.id):
                return self.api_response(
                    message="You do not have permission to access this notification.",
                    data=None,
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            return self.api_response(
                message="Notification marked as read.",
                data=NotificationSerializer(notification).data,
                status_code=status.HTTP_200_OK
            )


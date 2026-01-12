from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_session.read import CallSessionSerializer
from ai_calls.services.timebox_service import TimeboxService


class CallSessionDetailAPI(AuthAPI):
    """Get call session details."""
    permission_classes = [AiCallPermission]
    
    def get(self, request, session_id):
        call_session = CallSessionService.get_call_session(session_id)
        
        if not call_session:
            return self.api_response(
                message="Call session not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check object-level permission
        self.check_object_permissions(request, call_session)
        
        # Check time remaining
        time_info = TimeboxService.check_time_remaining(session_id)
        
        data = CallSessionSerializer(call_session).data
        data['time_remaining_seconds'] = time_info['remaining_seconds']
        data['warning_level'] = time_info['warning_level']
        
        return self.api_response(
            message="Call session retrieved successfully.",
            data=data,
            status_code=status.HTTP_200_OK
        )

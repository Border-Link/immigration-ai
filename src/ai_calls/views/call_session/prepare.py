from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_session.read import CallSessionSerializer


class CallSessionPrepareAPI(AuthAPI):
    """Prepare call session by building context bundle."""
    permission_classes = [AiCallPermission]
    
    def post(self, request, session_id):
        # Check object permission
        call_session = CallSessionService.get_call_session(session_id)
        if not call_session:
            return self.api_response(
                message="Call session not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        self.check_object_permissions(request, call_session)
        
        # Prepare call session
        call_session = CallSessionService.prepare_call_session(session_id)
        
        if not call_session:
            return self.api_response(
                message="Failed to prepare call session.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return self.api_response(
            message="Call session prepared successfully.",
            data=CallSessionSerializer(call_session).data,
            status_code=status.HTTP_200_OK
        )

from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_session.read import CallSessionSerializer


class CallSessionEndAPI(AuthAPI):
    """End the call normally."""
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
        
        # End call
        call_session = CallSessionService.end_call(session_id)
        
        if not call_session:
            return self.api_response(
                message="Failed to end call session.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        data = CallSessionSerializer(call_session).data
        if call_session.summary:
            from ai_calls.serializers.call_summary.read import CallSummarySerializer
            data['summary'] = CallSummarySerializer(call_session.summary).data
        
        return self.api_response(
            message="Call ended successfully.",
            data=data,
            status_code=status.HTTP_200_OK
        )

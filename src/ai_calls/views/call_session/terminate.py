from rest_framework import serializers, status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_session.read import CallSessionSerializer


class CallSessionTerminateSerializer(serializers.Serializer):
    """Serializer for terminating a call session."""
    reason = serializers.CharField(required=True, help_text="Reason for termination")


class CallSessionTerminateAPI(AuthAPI):
    """Terminate the call manually."""
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
        
        serializer = CallSessionTerminateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        call_session = CallSessionService.terminate_call(
            session_id=session_id,
            reason=serializer.validated_data.get('reason'),
            terminated_by_user_id=str(request.user.id)
        )
        
        if not call_session:
            return self.api_response(
                message="Failed to terminate call session.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return self.api_response(
            message="Call terminated successfully.",
            data=CallSessionSerializer(call_session).data,
            status_code=status.HTTP_200_OK
        )

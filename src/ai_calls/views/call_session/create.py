from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_session.create import CallSessionCreateSerializer
from ai_calls.serializers.call_session.read import CallSessionSerializer


class CallSessionCreateAPI(AuthAPI):
    """Create a new call session."""
    permission_classes = [AiCallPermission]
    
    def post(self, request):
        serializer = CallSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        parent_session_id = serializer.validated_data.get('parent_session_id')
        
        call_session = CallSessionService.create_call_session(
            case_id=str(serializer.validated_data.get('case_id')),
            user_id=str(request.user.id),
            parent_session_id=str(parent_session_id) if parent_session_id else None
        )
        
        if not call_session:
            error_message = 'Call session creation failed. Please verify case_id is valid and case is not closed.'
            if parent_session_id:
                error_message += ' Retries are only allowed if the previous call ended abruptly (within 10 minutes).'
            
            return self.api_response(
                message="Failed to create call session. Please check your input and try again.",
                data={'errors': {'general': error_message}},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return self.api_response(
            message="Call session created successfully.",
            data=CallSessionSerializer(call_session).data,
            status_code=status.HTTP_201_CREATED
        )

from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.call_session_service import CallSessionService
from ai_calls.serializers.call_transcript.read import CallTranscriptSerializer


class CallSessionTranscriptAPI(AuthAPI):
    """Get call session transcript."""
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
        
        # Get transcript
        transcripts = CallSessionService.get_transcript_turns(session_id)
        
        return self.api_response(
            message="Transcript retrieved successfully.",
            data={
                'turns': CallTranscriptSerializer(transcripts, many=True).data,
                'total_turns': transcripts.count()
            },
            status_code=status.HTTP_200_OK
        )

from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.ai_call_permission import AiCallPermission
from ai_calls.services.voice_orchestrator import VoiceOrchestrator
from ai_calls.services.timebox_service import TimeboxService


class CallSessionSpeechAPI(AuthAPI):
    """Process user speech and generate AI response."""
    permission_classes = [AiCallPermission]
    
    def post(self, request, session_id):
        # Check object permission
        from ai_calls.services.call_session_service import CallSessionService
        call_session = CallSessionService.get_call_session(session_id)
        if not call_session:
            return self.api_response(
                message="Call session not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        self.check_object_permissions(request, call_session)
        
        # Validate session is in progress
        if call_session.status != 'in_progress':
            return self.api_response(
                message=f"Call session is not in progress (status: {call_session.status}).",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get audio data from request
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return self.api_response(
                message="Audio file is required.",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Validate audio data size (max 10MB)
        if len(audio_data) > 10 * 1024 * 1024:
            return self.api_response(
                message="Audio file too large (max 10MB).",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate audio quality before processing
        from ai_calls.helpers.voice_utils import validate_audio_quality
        is_valid, error_message, audio_metadata = validate_audio_quality(audio_data)
        if not is_valid:
            return self.api_response(
                message=f"Audio validation failed: {error_message}",
                data={'audio_metadata': audio_metadata} if audio_metadata else None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Process user speech
        speech_result = VoiceOrchestrator.process_user_speech(audio_data, session_id)
        
        if 'error' in speech_result:
            return self.api_response(
                message=speech_result['error'],
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate AI response
        ai_response = VoiceOrchestrator.generate_ai_response(
            user_text=speech_result['text'],
            session_id=session_id
        )
        
        if 'error' in ai_response:
            return self.api_response(
                message=ai_response['error'],
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get time remaining
        time_info = TimeboxService.check_time_remaining(session_id)
        
        return self.api_response(
            message="Speech processed successfully.",
            data={
                'text': speech_result['text'],
                'confidence': speech_result['confidence'],
                'turn_id': speech_result['turn_id'],
                'ai_response': {
                    'text': ai_response['text'],
                    'audio_url': ai_response.get('audio_url'),
                    'turn_id': ai_response['turn_id'],
                    'guardrails_triggered': ai_response.get('guardrails_triggered', False)
                },
                'time_remaining_seconds': time_info['remaining_seconds'],
                'warning_level': time_info['warning_level']
            },
            status_code=status.HTTP_200_OK
        )

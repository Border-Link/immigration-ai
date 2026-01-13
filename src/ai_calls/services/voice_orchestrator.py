import logging
import json
import time
from typing import Dict, Any, Optional
from django.utils import timezone
from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector
from ai_calls.services.guardrails_service import GuardrailsService
from ai_calls.helpers.prompt_governance import compute_prompt_hash
from ai_calls.helpers.voice_utils import (
    validate_audio_quality,
    format_audio_for_stt,
    normalize_audio_for_stt,
    get_audio_metadata
)
from ai_calls.helpers.voice_prompts import (
    get_voice_ai_system_message,
    build_voice_ai_user_prompt,
    get_interruption_handling_message,
    get_error_recovery_message,
    get_empty_response_handling_message,
    get_low_confidence_handling_message,
    get_context_missing_message,
    get_session_inactive_message
)
from external_services.request.speech_client import (
    ExternalSpeechToTextClient,
    SpeechToTextError
)
from external_services.request.tts_client import (
    ExternalTextToSpeechClient,
    TextToSpeechError
)
from external_services.request.llm_client import ExternalLLMClient
from data_ingestion.helpers.llm_client import LLMClient
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)

logger = logging.getLogger('django')


class VoiceOrchestrator:
    """Service for voice orchestration (speech-to-text, text-to-speech, turn management)."""

    @staticmethod
    def process_user_speech(audio_data: bytes, session_id: str) -> Dict[str, Any]:
        """
        Process user speech input.
        
        Steps:
        1. Convert audio to text (speech-to-text service)
        2. Validate text quality
        3. Create CallTranscript entry (user turn)
        4. Return transcribed text
        
        Returns:
        - Dict with 'text', 'confidence', 'turn_id'
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.error(f"Call session {session_id} not found")
                return {'error': 'Call session not found'}
            
            if call_session.status != 'in_progress':
                logger.error(f"Call session {session_id} is not in_progress")
                return {'error': 'Call session is not active'}
            
            # Validate and normalize audio before processing
            normalized_audio, validation_error, audio_metadata = normalize_audio_for_stt(audio_data)
            if validation_error:
                logger.warning(f"Audio validation warning for session {session_id}: {validation_error}")
                # Continue with original audio, but log warning
            
            # Log audio metadata for debugging
            if audio_metadata:
                logger.debug(f"Audio metadata for session {session_id}: {audio_metadata}")
            
            # Speech-to-text using external service (with normalized audio)
            stt_result = VoiceOrchestrator._speech_to_text(normalized_audio, audio_metadata)
            
            if 'error' in stt_result:
                # Log audit event for STT failure
                from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='system_error',
                    description=f"Speech-to-text failed: {stt_result['error']}",
                    metadata={'error': stt_result['error']}
                )
                return {'error': stt_result['error']}
            
            text = stt_result.get('text', '').strip()
            confidence = stt_result.get('confidence', 0.0)
            
            if not text or len(text) == 0:
                error_msg = 'Speech recognition produced empty text. Please try speaking again.'
                logger.warning(f"Empty text from STT for session {session_id}")
                return {'error': error_msg}
            
            # Log low confidence and provide helpful message
            if confidence < 0.5:
                logger.warning(f"Low confidence speech recognition for session {session_id}: {confidence}")
                # Continue but include confidence info in response
                confidence_message = get_low_confidence_handling_message(confidence)
                # Note: We continue processing but could include this in response metadata
            
            # Create transcript entry (turn number assigned atomically)
            transcript = CallTranscriptRepository.create_transcript_turn(
                call_session=call_session,
                turn_type='user',
                text=text,
                speech_confidence=confidence
            )
            
            return {
                'text': text,
                'confidence': confidence,
                'turn_id': str(transcript.id)
            }
            
        except Exception as e:
            logger.error(f"Error processing user speech for session {session_id}: {e}")
            return {'error': str(e)}

    @staticmethod
    def _speech_to_text(audio_data: bytes, audio_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert audio to text using external speech-to-text service.
        
        Args:
            audio_data: Audio bytes (should be normalized/validated)
            audio_metadata: Optional audio metadata from validation
        
        Returns:
        - Dict with 'text', 'confidence', 'language_code', 'provider' or 'error'
        """
        try:
            # Extract sample rate from metadata if available
            sample_rate = 16000  # Default
            if audio_metadata and 'sample_rate' in audio_metadata:
                sample_rate = audio_metadata['sample_rate']
            
            stt_client = ExternalSpeechToTextClient()
            result = stt_client.transcribe(
                audio_data=audio_data,
                language_code='en-US',
                sample_rate=sample_rate
            )
            
            # Add audio metadata to result if available
            if audio_metadata:
                result['audio_metadata'] = audio_metadata
            
            return result
        except SpeechToTextError as e:
            logger.error(f"Speech-to-text error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('stt_failure', '')
            return {'error': error_msg, 'error_type': 'stt_error', 'original_error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in speech-to-text: {e}", exc_info=True)
            error_msg = get_error_recovery_message('stt_failure', '')
            return {'error': error_msg, 'error_type': 'stt_unexpected_error', 'original_error': str(e)}

    @staticmethod
    def generate_ai_response(user_text: str, session_id: str, store_prompt: bool = False) -> Dict[str, Any]:
        """
        Generate AI response to user input (REACTIVE-ONLY).
        
        IMPORTANT: AI never initiates conversation. This method is only called
        in response to user input.
        
        Steps:
        1. Pre-prompt guardrails: Validate user input against case scope
        2. Build AI prompt with context bundle (includes reactive-only instructions)
        3. Compute prompt hash (for audit trail)
        4. Call LLM API
        5. Post-response guardrails: Validate AI response for compliance
        6. Apply safety language if needed
        7. Create CallTranscript entry (AI turn)
           - Store prompt hash by default
           - Store full prompt only if store_prompt=True or guardrails triggered
        8. Convert text to speech
        9. Return audio + text
        
        Returns:
        - Dict with 'text', 'audio', 'turn_id', 'guardrails_triggered', 'prompt_hash'
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.error(f"Call session {session_id} not found")
                return {'error': 'Call session not found'}
            
            if call_session.status != 'in_progress':
                logger.error(f"Call session {session_id} is not in_progress")
                return {'error': 'Call session is not active'}
            
            if not call_session.context_bundle:
                logger.error(f"Call session {session_id} has no context bundle")
                error_msg = get_context_missing_message()
                return {'error': error_msg}
            
            # Pre-prompt guardrails (comprehensive validation)
            is_valid, error_message, action, violation_types = GuardrailsService.validate_user_input_pre_prompt(
                user_text,
                call_session.context_bundle
            )
            
            if not is_valid and action == 'refuse':
                # Return refusal message immediately (no AI call)
                # Use the error message from guardrails as the refusal text
                refusal_text = error_message if error_message else GuardrailsService.generate_refusal_message()
                
                # Check if should escalate
                should_escalate = GuardrailsService.should_escalate(violation_types or [])
                
                # Log refusal with violation details
                from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='refusal',
                    description=f"User question refused: {error_message}",
                    user_input=user_text,
                    metadata={
                        'violation_types': violation_types or [],
                        'action': action,
                        'escalated': should_escalate
                    }
                )
                
                # Update refusal count and escalation status
                from ai_calls.repositories.call_session_repository import CallSessionRepository
                update_fields = {
                    'refusals_count': call_session.refusals_count + 1
                }
                if should_escalate:
                    update_fields['escalated'] = True
                
                CallSessionRepository.update_call_session(
                    call_session,
                    **update_fields
                )
                
                return {
                    'text': refusal_text,
                    'audio': None,  # Would generate TTS
                    'guardrails_triggered': True,
                    'action': 'refused',
                    'violation_types': violation_types or [],
                    'escalated': should_escalate
                }
            
            # Build AI prompt
            prompt = VoiceOrchestrator._build_ai_prompt(user_text, call_session.context_bundle)
            prompt_hash = compute_prompt_hash(prompt) if prompt else None
            
            # Call LLM
            llm_result = VoiceOrchestrator._call_llm(prompt)
            
            if 'error' in llm_result:
                # Log audit event for LLM failure
                from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='system_error',
                    description=f"LLM call failed: {llm_result['error']}",
                    user_input=user_text,
                    metadata={'prompt_hash': prompt_hash, 'error': llm_result['error']}
                )
                
                # Mark session as failed if LLM is critical (only for persistent errors)
                # Don't fail on rate limits or temporary errors
                error_str = str(llm_result['error']).lower()
                if 'api key' in error_str or 'unauthorized' in error_str or 'service unavailable' in error_str:
                    from ai_calls.services.call_session_service import CallSessionService
                    CallSessionService.fail_call_session(
                        session_id=session_id,
                        reason=f"LLM service failure: {llm_result['error']}",
                        error_details={'user_input': user_text, 'prompt_hash': prompt_hash}
                    )
                
                return {'error': llm_result['error']}
            
            ai_response_text = llm_result.get('content', '').strip()
            ai_model = llm_result.get('model', 'unknown')
            
            # Handle empty or invalid responses
            if not ai_response_text or len(ai_response_text) == 0:
                logger.warning(f"Empty AI response for session {session_id}")
                error_msg = get_empty_response_handling_message()
                
                # Log this as an error
                from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='system_error',
                    description="AI generated empty response",
                    user_input=user_text,
                    metadata={'prompt_hash': prompt_hash, 'model': ai_model}
                )
                
                return {'error': error_msg}
            
            # Post-response guardrails (comprehensive validation)
            is_valid, error_message, action, violation_types = GuardrailsService.validate_ai_response_post_response(
                ai_response_text,
                call_session.context_bundle
            )
            
            guardrails_triggered = False
            if not is_valid:
                guardrails_triggered = True
                if action == 'sanitize':
                    # Use violation types directly from validation
                    ai_response_text = GuardrailsService.sanitize_ai_response(
                        ai_response_text,
                        violation_types or []
                    )
                
                # Check if should escalate
                should_escalate = GuardrailsService.should_escalate(violation_types or [])
                
                # Log guardrails trigger with detailed violation information
                from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
                CallAuditLogRepository.create_audit_log(
                    call_session=call_session,
                    event_type='guardrail_triggered',
                    description=f"Guardrails triggered: {error_message}",
                    user_input=user_text,
                    ai_response=ai_response_text,
                    metadata={
                        'violation_types': violation_types or [],
                        'action': action,
                        'escalated': should_escalate,
                        'severities': [
                            GuardrailsService.get_violation_severity(vt)
                            for vt in (violation_types or [])
                        ]
                    }
                )
                
                # Update warnings count and escalation status
                from ai_calls.repositories.call_session_repository import CallSessionRepository
                update_fields = {
                    'warnings_count': call_session.warnings_count + 1
                }
                if should_escalate:
                    update_fields['escalated'] = True
                
                CallSessionRepository.update_call_session(
                    call_session,
                    **update_fields
                )
            
            # Create transcript entry (turn number assigned atomically)
            transcript = CallTranscriptRepository.create_transcript_turn(
                call_session=call_session,
                turn_type='ai',
                text=ai_response_text,
                ai_model=ai_model,
                ai_prompt_hash=prompt_hash,
                ai_prompt_used=prompt if (store_prompt or guardrails_triggered) else None,
                guardrails_triggered=guardrails_triggered,
                guardrails_action=action if guardrails_triggered else None
            )
            
            # Text-to-speech
            tts_result = VoiceOrchestrator._text_to_speech(ai_response_text)
            
            # Update heartbeat to indicate active interaction
            from ai_calls.services.call_session_service import CallSessionService
            CallSessionService.update_heartbeat(session_id)
            
            # Prepare response
            response_data = {
                'text': ai_response_text,
                'turn_id': str(transcript.id),
                'guardrails_triggered': guardrails_triggered,
                'prompt_hash': prompt_hash,
                'ai_model': ai_model
            }
            
            if 'error' in tts_result:
                logger.warning(f"Text-to-speech failed for session {session_id}: {tts_result['error']}")
                response_data['audio_error'] = tts_result['error']
            else:
                # Include audio data or URL
                if 'audio_data' in tts_result:
                    # For real-time, audio_data is preferred
                    response_data['audio_data'] = tts_result['audio_data']
                    response_data['audio_content_type'] = tts_result.get('content_type', 'audio/mp3')
                elif 'audio_url' in tts_result:
                    response_data['audio_url'] = tts_result['audio_url']
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating AI response for session {session_id}: {e}")
            return {'error': str(e)}

    @staticmethod
    def _build_ai_prompt(user_text: str, context_bundle: Dict) -> str:
        """
        Build AI prompt with context bundle and reactive-only instructions.
        
        Uses comprehensive prompts from helpers to ensure all edge cases are covered.
        
        Args:
            user_text: The user's question or input
            context_bundle: The case context bundle (read-only, sealed)
            
        Returns:
            Formatted prompt string ready for LLM
        """
        return build_voice_ai_user_prompt(user_text, context_bundle)

    @staticmethod
    def _call_llm(prompt: str) -> Dict[str, Any]:
        """
        Call LLM API to generate response using external LLM client.
        
        Returns:
        - Dict with 'content', 'model', 'usage', 'processing_time_ms' or 'error'
        """
        try:
            # Use the internal LLMClient directly for better control
            # The ExternalLLMClient is more for rule extraction, we need chat completion
            from django.conf import settings
            
            llm_client = LLMClient()
            
            # Build messages for chat completion using comprehensive prompts
            system_message = get_voice_ai_system_message()
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            # Call LLM with appropriate settings for voice conversations
            response = llm_client.client.chat.completions.create(
                model=getattr(settings, 'AI_CALLS_LLM_MODEL', 'gpt-4o-mini'),
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent responses
                max_tokens=500,  # Shorter responses for voice
                timeout=10.0  # Timeout for real-time conversations
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            
            return {
                'content': content,
                'model': getattr(settings, 'AI_CALLS_LLM_MODEL', 'gpt-4o-mini'),
                'usage': {
                    'prompt_tokens': usage.prompt_tokens if usage else 0,
                    'completion_tokens': usage.completion_tokens if usage else 0,
                    'total_tokens': usage.total_tokens if usage else 0
                }
            }
            
        except LLMRateLimitError as e:
            logger.error(f"LLM rate limit error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('rate_limit', '')
            return {'error': error_msg, 'error_type': 'rate_limit', 'retry_after': 60}
        except LLMTimeoutError as e:
            logger.error(f"LLM timeout error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('timeout', '')
            return {'error': error_msg, 'error_type': 'timeout'}
        except LLMServiceUnavailableError as e:
            logger.error(f"LLM service unavailable: {e}", exc_info=True)
            error_msg = get_error_recovery_message('llm_failure', '')
            return {'error': error_msg, 'error_type': 'service_unavailable'}
        except LLMAPIKeyError as e:
            logger.error(f"LLM API key error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('llm_failure', '')
            return {'error': error_msg, 'error_type': 'api_key_error'}
        except LLMInvalidResponseError as e:
            logger.error(f"LLM invalid response error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('llm_failure', '')
            return {'error': error_msg, 'error_type': 'invalid_response'}
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}", exc_info=True)
            error_msg = get_error_recovery_message('llm_failure', '')
            return {'error': error_msg, 'error_type': 'unexpected_error'}

    @staticmethod
    def _text_to_speech(text: str) -> Dict[str, Any]:
        """
        Convert text to speech using external text-to-speech service.
        
        Returns:
        - Dict with 'audio_data', 'content_type', 'provider' or 'error'
        Note: For real-time, 'audio_data' is returned directly (not URL)
        """
        try:
            tts_client = ExternalTextToSpeechClient()
            result = tts_client.synthesize(
                text=text,
                language_code='en-US',
                audio_encoding='MP3',
                speaking_rate=1.0,
                pitch=0.0
            )
            return result
        except TextToSpeechError as e:
            logger.error(f"Text-to-speech error: {e}", exc_info=True)
            error_msg = get_error_recovery_message('tts_failure', '')
            return {'error': error_msg, 'error_type': 'tts_error', 'original_error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in text-to-speech: {e}", exc_info=True)
            error_msg = get_error_recovery_message('tts_failure', '')
            return {'error': error_msg, 'error_type': 'tts_unexpected_error', 'original_error': str(e)}

    @staticmethod
    def handle_interruption(session_id: str, current_turn_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle user interruption during AI response.
        
        When a user interrupts the AI (e.g., by speaking while AI is responding),
        this method handles the interruption gracefully.
        
        Steps:
        1. Validate session is active
        2. Log interruption event
        3. Cancel any ongoing TTS generation (if applicable)
        4. Prepare for new user input
        5. Return interruption acknowledgment
        
        Args:
            session_id: Call session ID
            current_turn_id: Optional current AI turn ID being interrupted
            
        Returns:
            Dict with 'acknowledged', 'message', 'ready_for_input'
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.error(f"Call session {session_id} not found for interruption")
                return {
                    'acknowledged': False,
                    'error': 'Call session not found'
                }
            
            if call_session.status != 'in_progress':
                logger.warning(f"Interruption attempted on non-active session {session_id} (status: {call_session.status})")
                return {
                    'acknowledged': False,
                    'error': get_session_inactive_message(call_session.status)
                }
            
            # Log interruption event
            from ai_calls.repositories.call_audit_log_repository import CallAuditLogRepository
            CallAuditLogRepository.create_audit_log(
                call_session=call_session,
                event_type='interruption',
                description=f"User interrupted AI response (turn_id: {current_turn_id})",
                metadata={
                    'interrupted_turn_id': current_turn_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # If there's a current turn, we could mark it as interrupted
            # (This would require adding an 'interrupted' field to CallTranscript model)
            # For now, we just log it
            
            # Update heartbeat to indicate active interaction
            from ai_calls.services.call_session_service import CallSessionService
            CallSessionService.update_heartbeat(session_id)
            
            interruption_message = get_interruption_handling_message()
            
            logger.info(f"Interruption handled for session {session_id}, turn {current_turn_id}")
            
            return {
                'acknowledged': True,
                'message': interruption_message,
                'ready_for_input': True,
                'interrupted_turn_id': current_turn_id
            }
            
        except Exception as e:
            logger.error(f"Error handling interruption for session {session_id}: {e}", exc_info=True)
            return {
                'acknowledged': False,
                'error': f"Error handling interruption: {str(e)}"
            }

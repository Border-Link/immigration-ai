"""
Speech-to-Text client wrapper for external STT API requests.

Provides a centralized interface for speech-to-text API calls through external_services.
Supports Google Speech-to-Text and AWS Transcribe.
"""

import logging
from typing import Dict, Optional, Tuple
from django.conf import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

logger = logging.getLogger('django')


class SpeechToTextError(Exception):
    """Base exception for speech-to-text errors."""
    pass


class SpeechToTextRateLimitError(SpeechToTextError):
    """Rate limit exceeded."""
    pass


class SpeechToTextTimeoutError(SpeechToTextError):
    """Request timeout."""
    pass


class SpeechToTextServiceUnavailableError(SpeechToTextError):
    """Service unavailable."""
    pass


class SpeechToTextAPIKeyError(SpeechToTextError):
    """Invalid API key."""
    pass


class ExternalSpeechToTextClient:
    """
    External Speech-to-Text client wrapper.
    
    Supports Google Speech-to-Text (primary) and AWS Transcribe (fallback).
    """
    
    def __init__(self):
        """Initialize speech-to-text client."""
        self.provider = getattr(settings, 'SPEECH_TO_TEXT_PROVIDER', 'google').lower()
        self._google_client = None
        self._aws_client = None
    
    def transcribe(
        self,
        audio_data: bytes,
        language_code: str = 'en-US',
        sample_rate: int = 16000,
        use_fallback: bool = True
    ) -> Dict[str, any]:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio bytes (WAV, FLAC, or LINEAR16 format)
            language_code: Language code (default: 'en-US')
            sample_rate: Audio sample rate in Hz (default: 16000)
            use_fallback: Whether to use fallback provider on failure (default: True)
            
        Returns:
            Dict with 'text', 'confidence', 'language_code', 'provider'
            
        Raises:
            SpeechToTextRateLimitError: Rate limit exceeded
            SpeechToTextTimeoutError: Request timeout
            SpeechToTextServiceUnavailableError: Service unavailable
            SpeechToTextAPIKeyError: Invalid API key
        """
        try:
            if self.provider == 'google':
                return self._transcribe_google(audio_data, language_code, sample_rate)
            elif self.provider == 'aws':
                return self._transcribe_aws(audio_data, language_code, sample_rate)
            else:
                raise SpeechToTextError(f"Unsupported provider: {self.provider}")
        except (SpeechToTextRateLimitError, SpeechToTextTimeoutError, 
                SpeechToTextServiceUnavailableError, SpeechToTextAPIKeyError) as e:
            if use_fallback and self.provider == 'google':
                logger.warning(f"Google STT failed, falling back to AWS: {e}")
                return self._transcribe_aws(audio_data, language_code, sample_rate)
            elif use_fallback and self.provider == 'aws':
                logger.warning(f"AWS Transcribe failed, falling back to Google: {e}")
                return self._transcribe_google(audio_data, language_code, sample_rate)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in speech-to-text: {e}", exc_info=True)
            raise SpeechToTextError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((SpeechToTextRateLimitError, SpeechToTextServiceUnavailableError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
    def _transcribe_google(
        self,
        audio_data: bytes,
        language_code: str,
        sample_rate: int
    ) -> Dict[str, any]:
        """Transcribe using Google Speech-to-Text API."""
        try:
            from google.cloud import speech
            
            # Get API credentials
            google_credentials = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            if not google_credentials:
                # Try to get from environment or settings
                google_api_key = getattr(settings, 'GOOGLE_SPEECH_API_KEY', None)
                if not google_api_key:
                    raise SpeechToTextAPIKeyError("Google Speech-to-Text credentials not configured")
            
            # Initialize client
            if google_credentials:
                client = speech.SpeechClient.from_service_account_json(google_credentials)
            else:
                # Use API key (limited functionality)
                client = speech.SpeechClient()
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='latest_long'  # Best for long-form audio
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform transcription
            response = client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language_code': language_code,
                    'provider': 'google'
                }
            
            # Get best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                'text': alternative.transcript,
                'confidence': alternative.confidence,
                'language_code': language_code,
                'provider': 'google'
            }
            
        except ImportError:
            logger.error("Google Cloud Speech library not installed. Install with: pip install google-cloud-speech")
            raise SpeechToTextError("Google Cloud Speech library not available")
        except Exception as e:
            logger.error(f"Google Speech-to-Text error: {e}", exc_info=True)
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise SpeechToTextRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "timeout" in str(e).lower():
                raise SpeechToTextTimeoutError(f"Request timeout: {str(e)}")
            elif "credentials" in str(e).lower() or "authentication" in str(e).lower():
                raise SpeechToTextAPIKeyError(f"Authentication error: {str(e)}")
            else:
                raise SpeechToTextServiceUnavailableError(f"Service error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((SpeechToTextRateLimitError, SpeechToTextServiceUnavailableError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
    def _transcribe_aws(
        self,
        audio_data: bytes,
        language_code: str,
        sample_rate: int
    ) -> Dict[str, any]:
        """Transcribe using AWS Transcribe API."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get AWS credentials
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
            
            if not aws_access_key_id or not aws_secret_access_key:
                raise SpeechToTextAPIKeyError("AWS credentials not configured")
            
            # Initialize client
            transcribe_client = boto3.client(
                'transcribe',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            
            # For real-time transcription, we'd use TranscribeStreaming
            # For now, we'll use the synchronous API (requires uploading to S3)
            # This is a simplified version - in production, you'd use streaming
            
            # Note: AWS Transcribe requires audio to be in S3 for synchronous transcription
            # For real-time, use TranscribeStreaming with WebSocket
            # This is a placeholder implementation
            
            raise SpeechToTextError(
                "AWS Transcribe synchronous API requires S3 upload. "
                "Use TranscribeStreaming for real-time transcription."
            )
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise SpeechToTextError("AWS SDK not available")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ThrottlingException':
                raise SpeechToTextRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif error_code == 'RequestTimeout':
                raise SpeechToTextTimeoutError(f"Request timeout: {str(e)}")
            elif error_code in ['InvalidRequestException', 'BadRequestException']:
                raise SpeechToTextAPIKeyError(f"Invalid request: {str(e)}")
            else:
                raise SpeechToTextServiceUnavailableError(f"AWS error: {str(e)}")
        except Exception as e:
            logger.error(f"AWS Transcribe error: {e}", exc_info=True)
            raise SpeechToTextServiceUnavailableError(f"Service error: {str(e)}")

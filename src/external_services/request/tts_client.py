"""
Text-to-Speech client wrapper for external TTS API requests.

Provides a centralized interface for text-to-speech API calls through external_services.
Supports Google Text-to-Speech and AWS Polly.
"""

import logging
from typing import Dict, Optional
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


class TextToSpeechError(Exception):
    """Base exception for text-to-speech errors."""
    pass


class TextToSpeechRateLimitError(TextToSpeechError):
    """Rate limit exceeded."""
    pass


class TextToSpeechTimeoutError(TextToSpeechError):
    """Request timeout."""
    pass


class TextToSpeechServiceUnavailableError(TextToSpeechError):
    """Service unavailable."""
    pass


class TextToSpeechAPIKeyError(TextToSpeechError):
    """Invalid API key."""
    pass


class ExternalTextToSpeechClient:
    """
    External Text-to-Speech client wrapper.
    
    Supports Google Text-to-Speech (primary) and AWS Polly (fallback).
    """
    
    def __init__(self):
        """Initialize text-to-speech client."""
        self.provider = getattr(settings, 'TEXT_TO_SPEECH_PROVIDER', 'google').lower()
        self._google_client = None
        self._aws_client = None
    
    def synthesize(
        self,
        text: str,
        language_code: str = 'en-US',
        voice_name: Optional[str] = None,
        ssml_gender: str = 'NEUTRAL',
        audio_encoding: str = 'MP3',
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        use_fallback: bool = True
    ) -> Dict[str, any]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            language_code: Language code (default: 'en-US')
            voice_name: Optional voice name (e.g., 'en-US-Standard-B')
            ssml_gender: Gender for voice (MALE, FEMALE, NEUTRAL)
            audio_encoding: Audio format (MP3, LINEAR16, OGG_OPUS)
            speaking_rate: Speaking rate (0.25 to 4.0, default: 1.0)
            pitch: Pitch adjustment (-20.0 to 20.0 semitones, default: 0.0)
            use_fallback: Whether to use fallback provider on failure (default: True)
            
        Returns:
            Dict with 'audio_url', 'audio_data', 'content_type', 'provider'
            Note: For real-time, 'audio_data' is preferred over 'audio_url'
            
        Raises:
            TextToSpeechRateLimitError: Rate limit exceeded
            TextToSpeechTimeoutError: Request timeout
            TextToSpeechServiceUnavailableError: Service unavailable
            TextToSpeechAPIKeyError: Invalid API key
        """
        try:
            if self.provider == 'google':
                return self._synthesize_google(
                    text, language_code, voice_name, ssml_gender,
                    audio_encoding, speaking_rate, pitch
                )
            elif self.provider == 'aws':
                return self._synthesize_aws(
                    text, language_code, voice_name,
                    audio_encoding, speaking_rate, pitch
                )
            else:
                raise TextToSpeechError(f"Unsupported provider: {self.provider}")
        except (TextToSpeechRateLimitError, TextToSpeechTimeoutError,
                TextToSpeechServiceUnavailableError, TextToSpeechAPIKeyError) as e:
            if use_fallback and self.provider == 'google':
                logger.warning(f"Google TTS failed, falling back to AWS: {e}")
                return self._synthesize_aws(
                    text, language_code, voice_name,
                    audio_encoding, speaking_rate, pitch
                )
            elif use_fallback and self.provider == 'aws':
                logger.warning(f"AWS Polly failed, falling back to Google: {e}")
                return self._synthesize_google(
                    text, language_code, voice_name, ssml_gender,
                    audio_encoding, speaking_rate, pitch
                )
            raise
        except Exception as e:
            logger.error(f"Unexpected error in text-to-speech: {e}", exc_info=True)
            raise TextToSpeechError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TextToSpeechRateLimitError, TextToSpeechServiceUnavailableError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
    def _synthesize_google(
        self,
        text: str,
        language_code: str,
        voice_name: Optional[str],
        ssml_gender: str,
        audio_encoding: str,
        speaking_rate: float,
        pitch: float
    ) -> Dict[str, any]:
        """Synthesize using Google Text-to-Speech API."""
        try:
            from google.cloud import texttospeech
            
            # Get API credentials
            google_credentials = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            if not google_credentials:
                google_api_key = getattr(settings, 'GOOGLE_TTS_API_KEY', None)
                if not google_api_key:
                    raise TextToSpeechAPIKeyError("Google Text-to-Speech credentials not configured")
            
            # Initialize client
            if google_credentials:
                client = texttospeech.TextToSpeechClient.from_service_account_json(google_credentials)
            else:
                client = texttospeech.TextToSpeechClient()
            
            # Configure voice
            if voice_name:
                voice = texttospeech.VoiceSelectionParams(
                    name=voice_name,
                    language_code=language_code
                )
            else:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    ssml_gender=getattr(texttospeech.SsmlVoiceGender, ssml_gender, texttospeech.SsmlVoiceGender.NEUTRAL)
                )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=getattr(
                    texttospeech.AudioEncoding,
                    audio_encoding.upper(),
                    texttospeech.AudioEncoding.MP3
                ),
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            
            # Synthesize
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # For real-time, return audio data directly
            # In production, you might store in S3 and return URL, or stream directly
            return {
                'audio_data': response.audio_content,
                'content_type': f'audio/{audio_encoding.lower()}',
                'provider': 'google',
                'language_code': language_code
            }
            
        except ImportError:
            logger.error("Google Cloud TTS library not installed. Install with: pip install google-cloud-texttospeech")
            raise TextToSpeechError("Google Cloud TTS library not available")
        except Exception as e:
            logger.error(f"Google Text-to-Speech error: {e}", exc_info=True)
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise TextToSpeechRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "timeout" in str(e).lower():
                raise TextToSpeechTimeoutError(f"Request timeout: {str(e)}")
            elif "credentials" in str(e).lower() or "authentication" in str(e).lower():
                raise TextToSpeechAPIKeyError(f"Authentication error: {str(e)}")
            else:
                raise TextToSpeechServiceUnavailableError(f"Service error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TextToSpeechRateLimitError, TextToSpeechServiceUnavailableError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
    def _synthesize_aws(
        self,
        text: str,
        language_code: str,
        voice_name: Optional[str],
        audio_encoding: str,
        speaking_rate: float,
        pitch: float
    ) -> Dict[str, any]:
        """Synthesize using AWS Polly API."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get AWS credentials
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
            
            if not aws_access_key_id or not aws_secret_access_key:
                raise TextToSpeechAPIKeyError("AWS credentials not configured")
            
            # Initialize client
            polly_client = boto3.client(
                'polly',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            
            # Map voice name or use default
            if not voice_name:
                # Default voice for language
                if 'en' in language_code.lower():
                    voice_name = 'Joanna'  # Neural voice
                else:
                    voice_name = 'Joanna'
            
            # Map audio encoding
            output_format_map = {
                'MP3': 'mp3',
                'OGG_OPUS': 'ogg_vorbis',
                'LINEAR16': 'pcm'
            }
            output_format = output_format_map.get(audio_encoding.upper(), 'mp3')
            
            # Synthesize
            response = polly_client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_name,
                Engine='neural',  # Use neural engine for better quality
                TextType='text'
            )
            
            # Read audio stream
            audio_data = response['AudioStream'].read()
            
            return {
                'audio_data': audio_data,
                'content_type': f'audio/{output_format}',
                'provider': 'aws',
                'language_code': language_code
            }
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise TextToSpeechError("AWS SDK not available")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ThrottlingException':
                raise TextToSpeechRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif error_code == 'RequestTimeout':
                raise TextToSpeechTimeoutError(f"Request timeout: {str(e)}")
            elif error_code in ['InvalidRequestException', 'BadRequestException']:
                raise TextToSpeechAPIKeyError(f"Invalid request: {str(e)}")
            else:
                raise TextToSpeechServiceUnavailableError(f"AWS error: {str(e)}")
        except Exception as e:
            logger.error(f"AWS Polly error: {e}", exc_info=True)
            raise TextToSpeechServiceUnavailableError(f"Service error: {str(e)}")

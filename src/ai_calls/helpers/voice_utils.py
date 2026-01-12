"""
Voice Utilities Helper

Comprehensive utility functions for voice processing, audio validation,
and format conversion for speech-to-text and text-to-speech services.
"""
import logging
import struct
import wave
import io
from typing import Tuple, Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger('django')

# Audio validation constants
MIN_AUDIO_DURATION_SECONDS = 0.1  # Minimum 100ms
MAX_AUDIO_DURATION_SECONDS = 60.0  # Maximum 60 seconds per chunk
MIN_SAMPLE_RATE = 8000  # Minimum sample rate (Hz)
MAX_SAMPLE_RATE = 48000  # Maximum sample rate (Hz)
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]
SUPPORTED_CHANNELS = [1, 2]  # Mono or stereo
SUPPORTED_BIT_DEPTHS = [16, 24, 32]  # Bits per sample

# Audio format constants
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1  # Mono
DEFAULT_BIT_DEPTH = 16
DEFAULT_FORMAT = 'wav'

# File size limits
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MIN_AUDIO_SIZE_BYTES = 100  # Minimum 100 bytes


class AudioValidationError(Exception):
    """Exception raised for audio validation errors."""
    pass


def validate_audio_quality(
    audio_data: bytes,
    min_duration: float = MIN_AUDIO_DURATION_SECONDS,
    max_duration: float = MAX_AUDIO_DURATION_SECONDS,
    min_sample_rate: int = MIN_SAMPLE_RATE,
    max_sample_rate: int = MAX_SAMPLE_RATE
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Comprehensive audio quality validation.
    
    Validates:
    - File size (not too small or too large)
    - Audio format (WAV, FLAC, etc.)
    - Sample rate (within acceptable range)
    - Duration (not too short or too long)
    - Channels (mono or stereo)
    - Bit depth (16-bit, 24-bit, or 32-bit)
    - Audio content (not silent/corrupted)
    
    Args:
        audio_data: Audio file bytes
        min_duration: Minimum audio duration in seconds
        max_duration: Maximum audio duration in seconds
        min_sample_rate: Minimum acceptable sample rate
        max_sample_rate: Maximum acceptable sample rate
    
    Returns:
        Tuple of (is_valid, error_message, audio_metadata)
        audio_metadata: Dict with 'sample_rate', 'channels', 'duration', 'format', etc.
    """
    if not audio_data:
        return False, "Audio data is empty", None
    
    # Check file size
    audio_size = len(audio_data)
    if audio_size < MIN_AUDIO_SIZE_BYTES:
        return False, f"Audio file too small ({audio_size} bytes). Minimum: {MIN_AUDIO_SIZE_BYTES} bytes", None
    
    if audio_size > MAX_AUDIO_SIZE_BYTES:
        return False, f"Audio file too large ({audio_size / 1024 / 1024:.2f}MB). Maximum: {MAX_AUDIO_SIZE_BYTES / 1024 / 1024}MB", None
    
    # Try to detect and parse audio format
    audio_metadata = {}
    
    # Check if it's WAV format
    if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
        try:
            metadata = _parse_wav_format(audio_data)
            audio_metadata.update(metadata)
        except Exception as e:
            logger.warning(f"Error parsing WAV format: {e}")
            return False, f"Invalid WAV format: {str(e)}", None
    elif audio_data[:4] == b'fLaC':
        # FLAC format
        try:
            metadata = _parse_flac_format(audio_data)
            audio_metadata.update(metadata)
            audio_metadata['format'] = 'flac'
        except Exception as e:
            logger.warning(f"Error parsing FLAC format: {e}")
            return False, f"Invalid FLAC format: {str(e)}", None
    elif audio_data[:4] == b'OggS':
        # OGG format
        audio_metadata['format'] = 'ogg'
        # OGG parsing is complex, use default values
        audio_metadata['sample_rate'] = DEFAULT_SAMPLE_RATE
        audio_metadata['channels'] = DEFAULT_CHANNELS
        audio_metadata['bit_depth'] = DEFAULT_BIT_DEPTH
    else:
        # Unknown format - try to use defaults
        logger.warning(f"Unknown audio format, using defaults")
        audio_metadata['format'] = 'unknown'
        audio_metadata['sample_rate'] = DEFAULT_SAMPLE_RATE
        audio_metadata['channels'] = DEFAULT_CHANNELS
        audio_metadata['bit_depth'] = DEFAULT_BIT_DEPTH
    
    # Validate sample rate
    sample_rate = audio_metadata.get('sample_rate', DEFAULT_SAMPLE_RATE)
    if sample_rate < min_sample_rate or sample_rate > max_sample_rate:
        return False, f"Sample rate {sample_rate}Hz out of range ({min_sample_rate}-{max_sample_rate}Hz)", audio_metadata
    
    if sample_rate not in SUPPORTED_SAMPLE_RATES:
        logger.warning(f"Unusual sample rate: {sample_rate}Hz (supported: {SUPPORTED_SAMPLE_RATES})")
    
    # Validate channels
    channels = audio_metadata.get('channels', DEFAULT_CHANNELS)
    if channels not in SUPPORTED_CHANNELS:
        return False, f"Unsupported number of channels: {channels} (supported: {SUPPORTED_CHANNELS})", audio_metadata
    
    # Validate bit depth
    bit_depth = audio_metadata.get('bit_depth', DEFAULT_BIT_DEPTH)
    if bit_depth not in SUPPORTED_BIT_DEPTHS:
        logger.warning(f"Unusual bit depth: {bit_depth} bits (supported: {SUPPORTED_BIT_DEPTHS})")
    
    # Validate duration
    duration = audio_metadata.get('duration', 0)
    if duration < min_duration:
        return False, f"Audio too short ({duration:.2f}s). Minimum: {min_duration}s", audio_metadata
    
    if duration > max_duration:
        return False, f"Audio too long ({duration:.2f}s). Maximum: {max_duration}s", audio_metadata
    
    # Check for silence (basic check - very low amplitude)
    if not _check_audio_has_content(audio_data):
        logger.warning("Audio appears to be silent or have very low amplitude")
        # Don't fail, but log warning
    
    return True, None, audio_metadata


def _parse_wav_format(audio_data: bytes) -> Dict[str, Any]:
    """Parse WAV file format and extract metadata."""
    try:
        with io.BytesIO(audio_data) as wav_file:
            with wave.open(wav_file, 'rb') as wav:
                sample_rate = wav.getframerate()
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()  # Bytes per sample
                bit_depth = sample_width * 8
                frames = wav.getnframes()
                duration = frames / sample_rate if sample_rate > 0 else 0
                
                return {
                    'format': 'wav',
                    'sample_rate': sample_rate,
                    'channels': channels,
                    'bit_depth': bit_depth,
                    'sample_width': sample_width,
                    'frames': frames,
                    'duration': duration,
                    'compression_type': wav.getcomptype(),
                    'compression_name': wav.getcompname()
                }
    except Exception as e:
        raise AudioValidationError(f"Error parsing WAV: {str(e)}")


def _parse_flac_format(audio_data: bytes) -> Dict[str, Any]:
    """Parse FLAC file format and extract metadata."""
    # FLAC format is more complex, basic parsing
    # In production, use a library like mutagen or pydub
    try:
        # FLAC header structure (simplified)
        # Bytes 4-7: METADATA_BLOCK_HEADER
        # We'll use defaults and estimate from file size
        estimated_duration = len(audio_data) / (DEFAULT_SAMPLE_RATE * DEFAULT_CHANNELS * (DEFAULT_BIT_DEPTH / 8))
        
        return {
            'format': 'flac',
            'sample_rate': DEFAULT_SAMPLE_RATE,  # Would need proper parsing
            'channels': DEFAULT_CHANNELS,
            'bit_depth': DEFAULT_BIT_DEPTH,
            'duration': estimated_duration
        }
    except Exception as e:
        raise AudioValidationError(f"Error parsing FLAC: {str(e)}")


def _check_audio_has_content(audio_data: bytes) -> bool:
    """
    Basic check if audio has content (not silent).
    
    Checks if audio has sufficient amplitude variation.
    This is a simple heuristic - in production, use proper audio analysis.
    """
    if len(audio_data) < 100:
        return False
    
    # Sample some bytes and check for variation
    # Skip header (first 44 bytes for WAV)
    sample_start = min(44, len(audio_data) // 10)
    sample_end = min(sample_start + 1000, len(audio_data))
    sample = audio_data[sample_start:sample_end]
    
    if len(sample) < 10:
        return True  # Too small to check
    
    # Check for variation in byte values
    byte_values = [b for b in sample]
    if len(set(byte_values)) < 5:  # Very little variation
        return False
    
    # Check amplitude (basic check)
    try:
        # Try to interpret as 16-bit samples
        samples = struct.unpack(f'<{len(sample)//2}h', sample[:len(sample)//2*2])
        max_amplitude = max(abs(s) for s in samples) if samples else 0
        # If max amplitude is very low, likely silent
        return max_amplitude > 100  # Threshold for silence detection
    except Exception:
        # If unpacking fails, assume it has content
        return True


def format_audio_for_stt(
    audio_data: bytes,
    target_format: str = 'wav',
    target_sample_rate: int = DEFAULT_SAMPLE_RATE,
    target_channels: int = DEFAULT_CHANNELS,
    target_bit_depth: int = DEFAULT_BIT_DEPTH
) -> Tuple[bytes, Optional[str]]:
    """
    Format audio data for speech-to-text service.
    
    Converts audio to required format, sample rate, channels, and bit depth.
    Most STT services prefer:
    - Format: WAV (LINEAR16) or FLAC
    - Sample rate: 16000 Hz
    - Channels: Mono (1 channel)
    - Bit depth: 16-bit
    
    Args:
        audio_data: Input audio bytes
        target_format: Target format ('wav', 'flac')
        target_sample_rate: Target sample rate (Hz)
        target_channels: Target number of channels (1=mono, 2=stereo)
        target_bit_depth: Target bit depth (16, 24, 32)
    
    Returns:
        Tuple of (formatted_audio_data, error_message)
    """
    if not audio_data:
        return b'', "Audio data is empty"
    
    try:
        # Validate input audio first
        is_valid, error_msg, metadata = validate_audio_quality(audio_data)
        if not is_valid:
            logger.warning(f"Input audio validation warning: {error_msg}")
            # Continue anyway, but log warning
        
        current_format = metadata.get('format', 'unknown') if metadata else 'unknown'
        current_sample_rate = metadata.get('sample_rate', DEFAULT_SAMPLE_RATE) if metadata else DEFAULT_SAMPLE_RATE
        current_channels = metadata.get('channels', DEFAULT_CHANNELS) if metadata else DEFAULT_CHANNELS
        
        # If already in target format and settings, return as-is
        if (current_format == target_format and
            current_sample_rate == target_sample_rate and
            current_channels == target_channels):
            return audio_data, None
        
        # Convert to target format
        if target_format == 'wav':
            return _convert_to_wav(
                audio_data,
                target_sample_rate,
                target_channels,
                target_bit_depth,
                current_format,
                current_sample_rate,
                current_channels
            )
        elif target_format == 'flac':
            # FLAC conversion would require additional library
            logger.warning("FLAC conversion not fully implemented, returning original")
            return audio_data, "FLAC conversion not fully implemented"
        else:
            return audio_data, f"Unsupported target format: {target_format}"
    
    except Exception as e:
        logger.error(f"Error formatting audio: {e}", exc_info=True)
        return audio_data, f"Error formatting audio: {str(e)}"


def _convert_to_wav(
    audio_data: bytes,
    target_sample_rate: int,
    target_channels: int,
    target_bit_depth: int,
    source_format: str,
    source_sample_rate: int,
    source_channels: int
) -> Tuple[bytes, Optional[str]]:
    """
    Convert audio to WAV format with target specifications.
    
    Note: Full audio conversion (resampling, channel conversion) requires
    libraries like pydub, librosa, or sox. This is a simplified version.
    """
    try:
        # If source is already WAV, try to read and rewrite
        if source_format == 'wav':
            try:
                with io.BytesIO(audio_data) as input_file:
                    with wave.open(input_file, 'rb') as wav_in:
                        # Read all frames
                        frames = wav_in.readframes(wav_in.getnframes())
                        in_sample_rate = wav_in.getframerate()
                        in_channels = wav_in.getnchannels()
                        in_sample_width = wav_in.getsampwidth()
                        
                        # Create output WAV
                        output = io.BytesIO()
                        with wave.open(output, 'wb') as wav_out:
                            # Set output parameters
                            wav_out.setnchannels(target_channels)
                            wav_out.setsampwidth(target_bit_depth // 8)
                            wav_out.setframerate(target_sample_rate)
                            
                            # If parameters match, just copy frames
                            if (in_sample_rate == target_sample_rate and
                                in_channels == target_channels and
                                in_sample_width == target_bit_depth // 8):
                                wav_out.writeframes(frames)
                            else:
                                # Parameters don't match - would need resampling/conversion
                                # For now, write as-is (may cause issues)
                                logger.warning(
                                    f"Audio conversion needed: {in_sample_rate}Hz/{in_channels}ch -> "
                                    f"{target_sample_rate}Hz/{target_channels}ch. Using original."
                                )
                                wav_out.setnchannels(in_channels)
                                wav_out.setsampwidth(in_sample_width)
                                wav_out.setframerate(in_sample_rate)
                                wav_out.writeframes(frames)
                        
                        output.seek(0)
                        return output.read(), None
            except Exception as e:
                logger.warning(f"Error converting WAV: {e}, returning original")
                return audio_data, f"WAV conversion warning: {str(e)}"
        
        # For non-WAV formats, create a basic WAV wrapper
        # In production, use proper audio conversion library
        logger.warning(f"Converting {source_format} to WAV - using basic conversion")
        return _create_basic_wav(audio_data, target_sample_rate, target_channels, target_bit_depth), None
    
    except Exception as e:
        logger.error(f"Error in WAV conversion: {e}", exc_info=True)
        return audio_data, f"Conversion error: {str(e)}"


def _create_basic_wav(
    audio_data: bytes,
    sample_rate: int,
    channels: int,
    bit_depth: int
) -> bytes:
    """
    Create a basic WAV file from raw audio data.
    
    This is a simplified version. In production, use proper audio processing.
    """
    output = io.BytesIO()
    
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(bit_depth // 8)
        wav.setframerate(sample_rate)
        # Write audio data (assuming it's already in correct format)
        wav.writeframes(audio_data)
    
    output.seek(0)
    return output.read()


def get_audio_metadata(audio_data: bytes) -> Dict[str, Any]:
    """
    Extract audio metadata without full validation.
    
    Returns:
        Dict with audio metadata (format, sample_rate, channels, duration, etc.)
    """
    if not audio_data:
        return {}
    
    try:
        _, _, metadata = validate_audio_quality(audio_data)
        return metadata or {}
    except Exception as e:
        logger.warning(f"Error extracting audio metadata: {e}")
        return {}


def estimate_audio_duration(
    audio_data: bytes,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
    bit_depth: int = DEFAULT_BIT_DEPTH
) -> float:
    """
    Estimate audio duration from file size and audio parameters.
    
    Args:
        audio_data: Audio file bytes
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bit depth (bits per sample)
    
    Returns:
        Estimated duration in seconds
    """
    if not audio_data:
        return 0.0
    
    # Account for file headers (approximate)
    header_size = 44  # Typical WAV header size
    audio_content_size = max(0, len(audio_data) - header_size)
    
    # Calculate: duration = bytes / (sample_rate * channels * bytes_per_sample)
    bytes_per_sample = bit_depth // 8
    bytes_per_second = sample_rate * channels * bytes_per_sample
    
    if bytes_per_second == 0:
        return 0.0
    
    duration = audio_content_size / bytes_per_second
    return max(0.0, duration)


def normalize_audio_for_stt(audio_data: bytes) -> Tuple[bytes, Optional[str], Dict[str, Any]]:
    """
    Normalize audio for speech-to-text processing.
    
    This is a convenience function that:
    1. Validates audio quality
    2. Formats audio for STT (WAV, 16kHz, mono, 16-bit)
    3. Returns formatted audio with metadata
    
    Args:
        audio_data: Input audio bytes
    
    Returns:
        Tuple of (formatted_audio, error_message, metadata)
    """
    # Validate first
    is_valid, error_msg, metadata = validate_audio_quality(audio_data)
    if not is_valid:
        return audio_data, error_msg, metadata or {}
    
    # Format for STT
    formatted_audio, format_error = format_audio_for_stt(
        audio_data,
        target_format='wav',
        target_sample_rate=DEFAULT_SAMPLE_RATE,
        target_channels=DEFAULT_CHANNELS,
        target_bit_depth=DEFAULT_BIT_DEPTH
    )
    
    if format_error:
        logger.warning(f"Audio formatting warning: {format_error}")
    
    return formatted_audio, format_error, metadata or {}

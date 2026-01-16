"""
Unit tests for voice utilities (audio validation/normalization).
"""

import io
import wave

import pytest


def _make_wav_bytes(
    *,
    duration_seconds: float = 0.2,
    sample_rate: int = 16000,
    channels: int = 1,
    sampwidth_bytes: int = 2,
    amplitude: int = 1000,
) -> bytes:
    """
    Create a simple PCM WAV in-memory.
    """
    frames = int(duration_seconds * sample_rate)
    # 16-bit little-endian samples
    if sampwidth_bytes != 2:
        raise ValueError("This helper only supports 16-bit samples (2 bytes).")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sampwidth_bytes)
        w.setframerate(sample_rate)
        # Create non-silent samples to avoid being classified as silent.
        sample = int(amplitude).to_bytes(2, byteorder="little", signed=True)
        w.writeframes(sample * frames * channels)
    buf.seek(0)
    return buf.read()


class TestVoiceUtilsValidateAudioQuality:
    def test_empty_audio_is_invalid(self):
        from ai_calls.helpers.voice_utils import validate_audio_quality

        ok, msg, meta = validate_audio_quality(b"")
        assert ok is False
        assert "empty" in (msg or "").lower()
        assert meta is None

    def test_too_small_audio_is_invalid(self):
        from ai_calls.helpers.voice_utils import validate_audio_quality

        ok, msg, meta = validate_audio_quality(b"x" * 10)
        assert ok is False
        assert "too small" in (msg or "").lower()
        assert meta is None

    def test_valid_wav_returns_metadata(self):
        from ai_calls.helpers.voice_utils import validate_audio_quality

        wav_bytes = _make_wav_bytes(duration_seconds=0.2, sample_rate=16000)
        ok, msg, meta = validate_audio_quality(wav_bytes)
        assert ok is True
        assert msg is None
        assert meta is not None
        assert meta["format"] == "wav"
        assert meta["sample_rate"] == 16000
        assert meta["channels"] == 1
        assert meta["duration"] >= 0.19

    def test_sample_rate_out_of_range_is_invalid(self):
        from ai_calls.helpers.voice_utils import validate_audio_quality

        wav_bytes = _make_wav_bytes(duration_seconds=0.2, sample_rate=5000)
        ok, msg, meta = validate_audio_quality(wav_bytes)
        assert ok is False
        assert "sample rate" in (msg or "").lower()
        assert meta is not None


class TestVoiceUtilsNormalizeAudioForStt:
    def test_normalize_returns_error_for_too_short_audio(self):
        from ai_calls.helpers.voice_utils import normalize_audio_for_stt

        wav_bytes = _make_wav_bytes(duration_seconds=0.05, sample_rate=16000)  # < 0.1s
        formatted, err, meta = normalize_audio_for_stt(wav_bytes)
        assert formatted == wav_bytes
        assert err is not None
        assert isinstance(meta, dict)


class TestVoiceUtilsEstimateDuration:
    def test_estimate_audio_duration_positive_for_wav(self):
        from ai_calls.helpers.voice_utils import estimate_audio_duration

        wav_bytes = _make_wav_bytes(duration_seconds=0.2, sample_rate=16000)
        d = estimate_audio_duration(wav_bytes, sample_rate=16000, channels=1, bit_depth=16)
        assert d > 0.0


class TestVoiceUtilsFormatAudioForStt:
    def test_format_audio_empty_returns_error(self):
        from ai_calls.helpers.voice_utils import format_audio_for_stt

        out, err = format_audio_for_stt(b"")
        assert out == b""
        assert err is not None

    def test_format_audio_returns_as_is_when_already_target(self):
        from ai_calls.helpers.voice_utils import format_audio_for_stt

        wav_bytes = _make_wav_bytes(duration_seconds=0.2, sample_rate=16000)
        out, err = format_audio_for_stt(wav_bytes, target_format="wav", target_sample_rate=16000, target_channels=1, target_bit_depth=16)
        assert err is None
        assert out == wav_bytes


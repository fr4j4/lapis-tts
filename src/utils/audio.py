"""
Audio utilities for in-memory audio processing.
"""
import io
import wave
import struct
import subprocess
import shutil
import logging
import numpy as np
from typing import Tuple

logger = logging.getLogger(__name__)


def _detect_sample_rate(audio_bytes: bytes) -> int:
    """
    Detect sample rate from WAV header bytes.

    Args:
        audio_bytes: WAV audio in bytes

    Returns:
        Sample rate or 22050 as fallback
    """
    if len(audio_bytes) < 44:
        return 22050
    try:
        sr = struct.unpack_from("<I", audio_bytes, 24)[0]
        if 8000 <= sr <= 192000:
            return sr
    except Exception:
        pass
    return 22050


def wav_bytes_to_numpy(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    """Convert WAV bytes to numpy array."""
    buffer = io.BytesIO(audio_bytes)
    with wave.open(buffer, "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        samp_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    if samp_width == 2:
        audio_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0
    else:
        audio_array = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32)
        audio_array = (audio_array - 128) / 128.0

    return audio_array, sample_rate


def numpy_to_wav_bytes(audio_array: np.ndarray, sample_rate: int = 22050) -> bytes:
    """Convert numpy array to WAV bytes."""
    audio_int16 = np.clip(audio_array * 32768.0, -32768, 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    return buffer.getvalue()


def concatenate_audio(audio_segments: list) -> bytes:
    """Concatenate multiple WAV audio segments, preserving the first segment's sample rate."""
    all_samples = []
    sample_rate = 22050

    for i, segment in enumerate(audio_segments):
        if isinstance(segment, bytes):
            samples, sr = wav_bytes_to_numpy(segment)
            if i == 0:
                sample_rate = sr
            all_samples.append(samples)
        elif isinstance(segment, np.ndarray):
            all_samples.append(segment)

    if not all_samples:
        return numpy_to_wav_bytes(np.array([], dtype=np.float32), sample_rate)

    combined = np.concatenate(all_samples)
    return numpy_to_wav_bytes(combined, sample_rate)


def add_silence(audio_bytes: bytes, duration: float = 0.2) -> bytes:
    """Add silence padding to the start and end of audio, matching the input sample rate."""
    samples, sr = wav_bytes_to_numpy(audio_bytes)
    silence_samples = int(duration * sr)
    silence = np.zeros(silence_samples, dtype=np.float32)

    combined = np.concatenate([silence, samples, silence])
    return numpy_to_wav_bytes(combined, sr)


def add_silence_at_end(audio_bytes: bytes, duration: float = 0.2) -> bytes:
    """Add silence padding to the end of audio only, matching the input sample rate."""
    samples, sr = wav_bytes_to_numpy(audio_bytes)
    silence_samples = int(duration * sr)
    silence = np.zeros(silence_samples, dtype=np.float32)

    combined = np.concatenate([samples, silence])
    return numpy_to_wav_bytes(combined, sr)


def apply_crossfade(audio1: bytes, audio2: bytes, fade_duration: float = 0.05) -> bytes:
    """
    Apply crossfade between two audio segments.
    
    Args:
        audio1: First audio segment
        audio2: Second audio segment  
        fade_duration: Crossfade duration in seconds (default 50ms)
    
    Returns:
        Audio with crossfade applied between segments
    """
    samples1, sr = wav_bytes_to_numpy(audio1)
    samples2, _ = wav_bytes_to_numpy(audio2)
    
    fade_samples = int(fade_duration * sr)
    
    if fade_samples >= len(samples1) or fade_samples >= len(samples2):
        fade_samples = min(len(samples1), len(samples2)) // 2
    
    if fade_samples <= 0:
        combined = np.concatenate([samples1, samples2])
        return numpy_to_wav_bytes(combined, sr)

    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    faded_segment1 = samples1[-fade_samples:] * fade_out
    faded_segment2 = samples2[:fade_samples] * fade_in

    middle = faded_segment1 + faded_segment2
    combined = np.concatenate([
        samples1[:-fade_samples],
        middle,
        samples2[fade_samples:]
    ])

    return numpy_to_wav_bytes(combined, sr)


def convert_audio_format(audio_bytes: bytes, output_format: str) -> bytes:
    """
    Convierte audio WAV a otro formato (ogg, mp3) usando FFmpeg.

    Args:
        audio_bytes: Audio WAV en bytes
        output_format: Formato de salida ('wav', 'ogg', 'mp3')

    Returns:
        Audio en el formato solicitado
    """
    if output_format == "wav":
        return audio_bytes

    if not shutil.which("ffmpeg"):
        logger.warning("ffmpeg no disponible, retornando audio sin convertir")
        return audio_bytes

    sample_rate, channels = _detect_sample_rate(audio_bytes), 1
    try:
        if len(audio_bytes) >= 24:
            channels = struct.unpack_from("<H", audio_bytes, 22)[0]
            sample_rate = struct.unpack_from("<I", audio_bytes, 24)[0]
            if not (1 <= channels <= 2 and 8000 <= sample_rate <= 192000):
                channels, sample_rate = 1, 22050
    except Exception:
        channels, sample_rate = 1, 22050

    if output_format == "ogg":
        codec = "libopus"
        container = "ogg"
    elif output_format == "mp3":
        codec = "libmp3lame"
        container = "mp3"
    else:
        logger.warning(f"Formato no soportado: {output_format}, retornando WAV")
        return audio_bytes

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "wav",
        "-i", "pipe:0",
        "-acodec", codec,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", container,
        "pipe:1",
    ]

    try:
        result = subprocess.run(
            cmd,
            input=audio_bytes,
            capture_output=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout:
            return result.stdout
        else:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            logger.error(f"ffmpeg conversión error ({output_format}): {error_msg}")
            return audio_bytes
    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timeout al convertir a {output_format}")
        return audio_bytes
    except Exception as e:
        logger.error(f"Error al convertir a {output_format}: {e}")
        return audio_bytes

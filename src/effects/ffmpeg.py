"""
FFmpeg effect processor.
Applies audio filter chains in memory.
"""
import struct
import subprocess
import logging
import shutil
from typing import Dict, Any, List, Tuple

from .base import EffectBase

logger = logging.getLogger(__name__)


def _detect_wav_format(audio_bytes: bytes) -> Tuple[int, int]:
    """
    Detect sample rate and channels from WAV header.

    Args:
        audio_bytes: WAV audio in bytes

    Returns:
        Tuple (sample_rate, channels) or (22050, 1) if detection fails
    """
    if len(audio_bytes) < 44:
        return 22050, 1

    try:
        channels = struct.unpack_from("<H", audio_bytes, 22)[0]
        sample_rate = struct.unpack_from("<I", audio_bytes, 24)[0]

        if 1 <= channels <= 2 and 8000 <= sample_rate <= 192000:
            return sample_rate, channels
    except Exception:
        pass

    return 22050, 1


class FFmpegEffect(EffectBase):
    """Apply audio effects using ffmpeg in memory."""

    name = "ffmpeg"
    effect_type = "ffmpeg"

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._available = self._check_available()

    def _check_available(self) -> bool:
        """Check if ffmpeg is available on the system."""
        return shutil.which(self.ffmpeg_path) is not None

    def apply(self, audio_bytes: bytes, config: Dict[str, Any]) -> bytes:
        """
        Apply effects to audio in memory using ffmpeg.

        Args:
            audio_bytes: WAV audio in bytes
            config: Dict with "filters" (list of ffmpeg filters)

        Returns:
            Processed audio in bytes
        """
        if not self._available:
            logger.warning("ffmpeg not available, returning unprocessed audio")
            return audio_bytes

        filters = config.get("filters", [])
        if not filters:
            return audio_bytes

        # Detect sample rate and channels from input
        sample_rate, channels = _detect_wav_format(audio_bytes)

        # Join filters with commas for ffmpeg
        filter_complex = ",".join(filters)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "wav",
            "-i", "pipe:0",
            "-af", filter_complex,
            "-f", "wav",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
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
                logger.error(f"ffmpeg error: {error_msg}")
                return audio_bytes
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timeout")
            return audio_bytes
        except Exception as e:
            logger.error(f"ffmpeg error: {e}")
            return audio_bytes

    def is_available(self) -> bool:
        """Check if ffmpeg is available."""
        return self._available

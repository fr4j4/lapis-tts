"""
Effects pipeline - applies effect chains and global effects.
Includes dynamic per-segment LUFS-based normalization.
"""
import logging
import struct
import subprocess
import shutil
import re
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from .registry import EffectsRegistry

logger = logging.getLogger(__name__)

# Default LUFS target for per-segment normalization
TARGET_LUFS = -16.0
# Gain limits to prevent artifacts
MIN_GAIN = -6.0
MAX_GAIN = +18.0


def _detect_wav_format(audio_bytes: bytes) -> Tuple[int, int]:
    """
    Detect sample rate and channels from WAV header.
    Reads standard WAV header bytes (offset 22-25 for sample rate,
    offset 22 for channels).

    Args:
        audio_bytes: WAV audio in bytes

    Returns:
        Tuple (sample_rate, channels) or (22050, 1) if detection fails
    """
    if len(audio_bytes) < 44:
        return 22050, 1

    try:
        # WAV header: offset 22 = channels (2 bytes), offset 24 = sample_rate (4 bytes)
        channels = struct.unpack_from("<H", audio_bytes, 22)[0]
        sample_rate = struct.unpack_from("<I", audio_bytes, 24)[0]

        # Validate reasonable ranges
        if 1 <= channels <= 2 and 8000 <= sample_rate <= 192000:
            return sample_rate, channels
    except Exception:
        pass

    return 22050, 1


class EffectsPipeline:
    """
    Audio effects processing pipeline.
    Handles per-segment effects and global effects (master bus).
    """

    def __init__(self, registry: EffectsRegistry, global_config: dict = None):
        self.registry = registry
        self.global_config = global_config or {}

    def process_segment(
        self,
        audio_bytes: bytes,
        mode: str,
        voice_config: Dict[str, Any]
    ) -> bytes:
        """
        Process an audio segment with mode-specific effects.

        Args:
            audio_bytes: Segment audio
            mode: Segment mode (normal, whisper, emphatic, etc.)
            voice_config: Voice configuration with modes

        Returns:
            Audio processed with mode effects
        """
        modes_config = voice_config.get("modes", {})
        mode_config = modes_config.get(mode, modes_config.get("normal", {}))
        effects_chain = mode_config.get("effects", [])

        if not effects_chain:
            return audio_bytes

        logger.info(f"[{mode}] Applying effects: {effects_chain}")
        processed = self.registry.apply_chain(audio_bytes, effects_chain)

        # Measure LUFS and normalize each segment dynamically
        processed = self._normalize_segment_dynamic(processed, mode)

        return processed

    def _get_normalization_params(self) -> tuple:
        """
        Get normalization parameters from master_bus.json.
        Falls back to hardcoded defaults if not configured.

        Returns:
            Tuple (target_lufs, min_gain, max_gain)
        """
        norm_config = self.global_config.get("normalization", {})
        target_lufs = norm_config.get("target_lufs", TARGET_LUFS)
        min_gain = norm_config.get("min_gain", MIN_GAIN)
        max_gain = norm_config.get("max_gain", MAX_GAIN)
        return target_lufs, min_gain, max_gain

    def _measure_lufs(self, audio_bytes: bytes) -> float:
        """
        Measure audio RMS level using ffmpeg volumedetect filter.
        For short segments, RMS is more reliable than integrated LUFS.

        Args:
            audio_bytes: WAV audio in bytes

        Returns:
            RMS level in dB (e.g. -18.5) or 0 if measurement fails
        """
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            return 0

        cmd = [
            ffmpeg_path,
            "-y",
            "-f", "wav",
            "-i", "pipe:0",
            "-af", "volumedetect",
            "-f", "null", "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                input=audio_bytes,
                capture_output=True,
                timeout=10,
            )
            stderr_text = result.stderr.decode("utf-8", errors="replace")

            # Parse: mean_volume: -18.5 dB
            match = re.search(r"mean_volume:\s+([-+]?\d+\.\d+)\s+dB", stderr_text)
            if match:
                rms_db = float(match.group(1))
                # Convert RMS to approximate LUFS (RMS + ~3dB ≈ LUFS for speech)
                estimated_lufs = rms_db + 3.0
                logger.info(f"Measured RMS: {rms_db:.1f} dB → est. LUFS: {estimated_lufs:.1f}")
                return estimated_lufs
            else:
                logger.warning(f"Could not parse RMS. stderr: {stderr_text[:300]}")
                return 0
        except Exception as e:
            logger.warning(f"Error measuring RMS: {e}")
            return 0

    def _normalize_segment_dynamic(self, audio_bytes: bytes, mode: str = "normal") -> bytes:
        """
        Normalize individual segment volume based on real LUFS measurement.

        Measures current LUFS, calculates required gain to reach TARGET_LUFS,
        and applies compression + limiter to even out levels.
        Normalization parameters are read from master_bus.json.

        Args:
            audio_bytes: Segment audio
            mode: Segment mode (for logging)

        Returns:
            Normalized audio
        """
        # 1. Measure current segment LUFS
        measured_lufs = self._measure_lufs(audio_bytes)

        # 2. Get parameters from master_bus.json
        target_lufs, min_gain, max_gain = self._get_normalization_params()

        # 3. Calculate required gain to reach target
        gain_needed = target_lufs - measured_lufs

        # 4. Clamp to prevent artifacts from extreme gain
        gain_needed = max(min_gain, min(max_gain, gain_needed))

        logger.info(f"[{mode}] LUFS: {measured_lufs:.1f} → Target: {target_lufs:.1f} → Gain: {gain_needed:+.1f}dB")

        # 5. Apply gain + compression + limiter
        normalize_filters = [
            f"volume={gain_needed:+.1f}dB",
            "acompressor=threshold=-24dB:ratio=5:attack=5:release=30",
            "alimiter=limit=-0.5dB:attack=3:release=20"
        ]

        return self._apply_ffmpeg_filters(audio_bytes, normalize_filters)

    def _apply_ffmpeg_filters(self, audio_bytes: bytes, filters: List[str]) -> bytes:
        """
        Apply audio filters using ffmpeg.
        Automatically detects and preserves the input audio sample rate.

        Args:
            audio_bytes: WAV audio in bytes
            filters: List of ffmpeg filters

        Returns:
            Processed audio
        """
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            return audio_bytes

        # Detect sample rate and channels from input audio
        sample_rate, channels = _detect_wav_format(audio_bytes)

        filter_complex = ",".join(filters)

        cmd = [
            ffmpeg_path,
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
                timeout=10,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                error_msg = result.stderr.decode("utf-8", errors="replace")
                logger.debug(f"ffmpeg error: {error_msg[:200]}")
        except subprocess.TimeoutExpired:
            logger.debug("ffmpeg timeout during audio processing")
        except Exception as e:
            logger.debug(f"ffmpeg error: {e}")

        return audio_bytes

    def process_global(
        self,
        audio_bytes: bytes,
        voice_config: Dict[str, Any]
    ) -> bytes:
        """
        Apply global effects to the complete audio.
        Combines voice-specific global_effects with master bus filters.
        Voice effects are applied first, then the master bus.

        Args:
            audio_bytes: Complete concatenated audio
            voice_config: Voice configuration with global_effects

        Returns:
            Audio with global effects applied
        """
        # 1. Apply voice-specific global_effects (effect names from registry)
        voice_global = voice_config.get("global_effects", [])
        if voice_global:
            logger.info(f"Applying voice global_effects: {voice_global}")
            audio_bytes = self.registry.apply_chain(audio_bytes, voice_global)

        # 2. Apply master bus (raw ffmpeg filters)
        master_config = self.global_config

        if not master_config.get("enabled", True):
            logger.info("Master bus disabled")
            return audio_bytes

        filters = master_config.get("filters", [])
        if not filters:
            logger.info("Master bus has no filters configured")
            return audio_bytes

        logger.info(f"Applying master bus: {len(filters)} filters")
        return self._apply_ffmpeg_filters(audio_bytes, filters)

    def process_full(
        self,
        segments: List[Dict[str, Any]],
        voice_config: Dict[str, Any]
    ) -> bytes:
        """
        Process complete segments with effects and concatenate.

        Args:
            segments: List of dicts with "audio" (bytes) and "mode" (str)
            voice_config: Voice configuration

        Returns:
            Final processed and concatenated audio
        """
        from ..utils.audio import concatenate_audio, add_silence, add_silence_at_end, apply_crossfade, wav_bytes_to_numpy, numpy_to_wav_bytes

        start_end_silence = self.global_config.get("start_end_silence", 0.1)
        crossfade_duration = voice_config.get("crossfade", self.global_config.get("crossfade", 0.05))
        segment_silence = voice_config.get("segment_silence", 0.15)
        processed_segments = []
        sample_rate = 22050

        for i, segment in enumerate(segments):
            audio = segment["audio"]
            mode = segment.get("mode", "normal")

            # Apply mode effects
            processed = self.process_segment(audio, mode, voice_config)

            # Apply silence based on position
            if i == 0:
                # First segment: silence at start
                if start_end_silence > 0:
                    processed = add_silence(processed, start_end_silence)
            elif i < len(segments) - 1:
                # Intermediate segments: silence between blocks + crossfade
                if segment_silence > 0:
                    processed = add_silence_at_end(processed, segment_silence)
            else:
                # Last segment: silence at end
                if start_end_silence > 0:
                    processed = add_silence_at_end(processed, start_end_silence)

            processed_segments.append(processed)

        # Concatenate with crossfade between segments
        if len(processed_segments) == 0:
            return numpy_to_wav_bytes(np.array([], dtype=np.float32), 22050)
        
        if len(processed_segments) == 1:
            combined = processed_segments[0]
            if isinstance(combined, bytes):
                _, sample_rate = wav_bytes_to_numpy(combined)
            elif isinstance(combined, np.ndarray):
                combined = numpy_to_wav_bytes(combined, sample_rate)
        else:
            combined, sample_rate = wav_bytes_to_numpy(processed_segments[0])
            for i in range(1, len(processed_segments)):
                if crossfade_duration > 0:
                    combined = apply_crossfade(
                        numpy_to_wav_bytes(combined, sample_rate),
                        processed_segments[i],
                        crossfade_duration
                    )
                    combined, sample_rate = wav_bytes_to_numpy(combined)
                else:
                    next_segment, _ = wav_bytes_to_numpy(processed_segments[i])
                    combined = np.concatenate([combined, next_segment])

        # Convert numpy array to bytes if needed
        if isinstance(combined, np.ndarray):
            combined = numpy_to_wav_bytes(combined, sample_rate)

        # Apply global effects
        final = self.process_global(combined, voice_config)

        return final

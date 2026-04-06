"""
TTS engine - PiperVoice wrapper for in-memory audio generation.
"""
import io
import wave
import logging
from pathlib import Path
from typing import Optional, Dict

from piper import PiperVoice
from piper.config import SynthesisConfig

logger = logging.getLogger(__name__)


class TTSEngine:
    """Speech synthesis engine using Piper."""

    def __init__(self, voices_dir: str):
        self.voices_dir = Path(voices_dir)
        self._voices: Dict[str, PiperVoice] = {}

    def load_voice(self, voice_id: str) -> Optional[PiperVoice]:
        """Load a voice model into memory."""
        if voice_id in self._voices:
            return self._voices[voice_id]

        model_path = self.voices_dir / f"{voice_id}.onnx"
        config_path = self.voices_dir / f"{voice_id}.onnx.json"

        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return None

        try:
            voice = PiperVoice.load(str(model_path), config_path=str(config_path))
            self._voices[voice_id] = voice
            logger.info(f"Voice loaded: {voice_id}")
            return voice
        except Exception as e:
            logger.error(f"Error loading voice {voice_id}: {e}")
            return None

    def synthesize(
        self,
        voice_id: str,
        text: str,
        length_scale: float = 1.0,
        noise_scale: float = 0.667,
        noise_w_scale: float = 0.8,
        speaker_id: Optional[int] = None,
    ) -> bytes:
        """Generate audio in memory as WAV bytes."""
        voice = self._voices.get(voice_id) or self.load_voice(voice_id)
        if not voice:
            raise ValueError(f"Voice not found: {voice_id}")

        # Create synthesis configuration
        syn_config = SynthesisConfig(
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w_scale,
        )

        # synthesize returns AudioChunk iterable
        chunks = list(voice.synthesize(text, syn_config=syn_config))

        if not chunks:
            raise ValueError(f"No audio generated for: {text}")

        # Build WAV from chunks
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(chunks[0].sample_rate)
            for chunk in chunks:
                wav_file.writeframes(chunk.audio_int16_bytes)

        return audio_buffer.getvalue()

    def list_voices(self) -> list:
        """List available voices in the directory."""
        voices = []
        if not self.voices_dir.exists():
            return voices

        for onnx_file in sorted(self.voices_dir.glob("*.onnx")):
            voice_id = onnx_file.stem
            config_file = self.voices_dir / f"{voice_id}.onnx.json"
            voices.append(
                {
                    "voice_id": voice_id,
                    "name": voice_id,
                    "file": str(onnx_file),
                    "config_exists": config_file.exists(),
                }
            )
        return voices

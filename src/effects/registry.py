"""
Effects registry - loads and manages effects from JSON files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import EffectBase
from .ffmpeg import FFmpegEffect

logger = logging.getLogger(__name__)


class EffectsRegistry:
    """
    Audio effects registry.
    Loads effect definitions from JSON files and applies them using processors.
    """

    def __init__(self, effects_dir: str, ffmpeg_path: str = "ffmpeg"):
        self.effects_dir = Path(effects_dir)
        self._effects: Dict[str, Dict[str, Any]] = {}
        self._processors: Dict[str, EffectBase] = {
            "ffmpeg": FFmpegEffect(ffmpeg_path=ffmpeg_path),
        }
        self._load_effects()

    def _load_effects(self):
        """Load all effect definitions from JSON files."""
        if not self.effects_dir.exists():
            logger.warning(f"Effects directory does not exist: {self.effects_dir}")
            return

        for json_file in sorted(self.effects_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    effect_def = json.load(f)
                
                name = effect_def.get("name", json_file.stem)
                self._effects[name] = effect_def
                logger.info(f"Effect loaded: {name} ({effect_def.get('type', 'unknown')})")
            except Exception as e:
                logger.error(f"Error loading effect {json_file}: {e}")

    def get_effect(self, name: str) -> Optional[Dict[str, Any]]:
        """Get effect definition by name."""
        return self._effects.get(name)

    def list_effects(self) -> List[str]:
        """List names of available effects."""
        return list(self._effects.keys())

    def apply_effect(self, audio_bytes: bytes, effect_name: str) -> bytes:
        """
        Apply an effect to audio.

        Args:
            audio_bytes: Audio in bytes
            effect_name: Name of the effect to apply

        Returns:
            Processed audio
        """
        effect_def = self._effects.get(effect_name)
        if not effect_def:
            logger.warning(f"Effect not found: {effect_name}")
            return audio_bytes

        effect_type = effect_def.get("type", "ffmpeg")
        processor = self._processors.get(effect_type)

        if not processor:
            logger.warning(f"Processor not available: {effect_type}")
            return audio_bytes

        return processor.apply(audio_bytes, effect_def)

    def apply_chain(self, audio_bytes: bytes, effect_names: List[str]) -> bytes:
        """
        Apply a chain of effects in sequence.

        Args:
            audio_bytes: Audio in bytes
            effect_names: List of effect names to apply in order

        Returns:
            Audio processed with the full chain
        """
        result = audio_bytes
        for effect_name in effect_names:
            result = self.apply_effect(result, effect_name)
        return result

    def has_effect(self, name: str) -> bool:
        """Check if an effect exists."""
        return name in self._effects

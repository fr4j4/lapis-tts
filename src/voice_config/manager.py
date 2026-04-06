"""
Voice configuration manager - loads and validates per-voice JSON configs.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VoiceConfigManager:
    """
    Manages per-voice configuration files.
    Each voice has its own JSON with model, params, modes, and global_effects.
    """

    def __init__(self, configs_dir: str):
        self.configs_dir = Path(configs_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_configs()

    def _load_configs(self):
        """Load all voice configuration JSON files."""
        if not self.configs_dir.exists():
            logger.warning(f"Voice configs directory does not exist: {self.configs_dir}")
            return

        for json_file in sorted(self.configs_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                errors = self._validate_config(config, json_file)
                if errors:
                    logger.error(f"Skipping invalid config {json_file.name}: {'; '.join(errors)}")
                    continue

                voice_id = config["voice_id"]
                self._configs[voice_id] = config
                logger.info(f"Voice config loaded: {voice_id}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {json_file}: {e}")
            except Exception as e:
                logger.error(f"Error loading config {json_file}: {e}")

    def _validate_config(self, config: dict, source: Path) -> list:
        """
        Validate a voice configuration structure.

        Args:
            config: Voice configuration dict
            source: Source file path for logging

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if "voice_id" not in config:
            errors.append("Missing required field 'voice_id'")

        if "name" not in config:
            errors.append("Missing required field 'name'")

        if "model" not in config:
            errors.append("Missing required field 'model'")

        if "params" not in config:
            errors.append("Missing required field 'params'")
        elif not isinstance(config["params"], dict):
            errors.append("'params' must be an object")
        else:
            params = config["params"]
            for key in ["length_scale", "noise_scale", "noise_w_scale"]:
                if key not in params:
                    errors.append(f"Missing '{key}' in params")
                elif not isinstance(params[key], (int, float)):
                    errors.append(f"'{key}' must be numeric")

        if "modes" not in config:
            errors.append("Missing required field 'modes'")
        elif not isinstance(config["modes"], dict):
            errors.append("'modes' must be an object")
        elif len(config["modes"]) == 0:
            errors.append("'modes' cannot be empty")
        else:
            for mode_name, mode_cfg in config["modes"].items():
                if not isinstance(mode_cfg, dict):
                    errors.append(f"Mode '{mode_name}' must be an object")
                elif "effects" not in mode_cfg:
                    errors.append(f"Mode '{mode_name}' missing 'effects'")
                elif not isinstance(mode_cfg["effects"], list):
                    errors.append(f"Mode '{mode_name}': 'effects' must be a list")

        if "global_effects" in config and not isinstance(config["global_effects"], list):
            errors.append("'global_effects' must be a list")

        if "segment_silence" in config and not isinstance(config["segment_silence"], (int, float)):
            errors.append("'segment_silence' must be numeric")

        return errors

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get full configuration for a voice."""
        return self._configs.get(voice_id)

    def list_voices(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List all available voices with summary info.
        
        Args:
            include_inactive: If True, include inactive voices. Default False.
        """
        voices = []
        for voice_id, config in self._configs.items():
            is_active = config.get("active", True)
            if not include_inactive and not is_active:
                continue
                
            voices.append({
                "voice_id": voice_id,
                "name": config.get("name", voice_id),
                "description": config.get("description", ""),
                "model": config.get("model", ""),
                "modes": list(config.get("modes", {}).keys()),
                "active": is_active,
            })
        return voices

    def has_voice(self, voice_id: str) -> bool:
        """Check if a voice_id is configured."""
        return voice_id in self._configs

    def get_modes(self, voice_id: str) -> List[str]:
        """Get available mode names for a voice."""
        config = self._configs.get(voice_id)
        if not config:
            return []
        return list(config.get("modes", {}).keys())

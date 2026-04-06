"""
Basic tests for LAPIS TTS Server.

Run with: pytest tests/ -v
"""
import pytest
import json


class TestVoiceConfigs:
    """Test voice configuration loading and structure."""

    def test_all_voice_configs_exist(self):
        """All voice config files should have corresponding voice models."""
        from pathlib import Path
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        voices_dir = Path(__file__).parent.parent / "voices"
        
        for config_file in configs_dir.glob("*.json"):
            with open(config_file) as f:
                config = json.load(f)
            
            model_name = config.get("model", "")
            if model_name:
                model_path = voices_dir / f"{model_name}.onnx"
                # Model file should exist (unless active: false)
                if config.get("active", True):
                    assert model_path.exists(), f"Model {model_name} not found for voice {config_file.name}"

    def test_voice_config_required_fields(self):
        """Each voice config should have all required fields."""
        from pathlib import Path
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        
        required_fields = ["voice_id", "name", "model", "params", "modes"]
        
        for config_file in configs_dir.glob("*.json"):
            with open(config_file) as f:
                config = json.load(f)
            
            for field in required_fields:
                assert field in config, f"Missing '{field}' in {config_file.name}"
            
            # Check params
            params = config.get("params", {})
            for param in ["length_scale", "noise_scale", "noise_w_scale"]:
                assert param in params, f"Missing '{param}' in {config_file.name}"

    def test_active_field_boolean(self):
        """The 'active' field should be a boolean if present."""
        from pathlib import Path
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        
        for config_file in configs_dir.glob("*.json"):
            with open(config_file) as f:
                config = json.load(f)
            
            if "active" in config:
                assert isinstance(config["active"], bool), f"'active' should be boolean in {config_file.name}"


class TestEffectsConfig:
    """Test effects configuration."""

    def test_all_effects_have_required_fields(self):
        """Each effect config should have required fields."""
        from pathlib import Path
        effects_dir = Path(__file__).parent.parent / "effects"
        
        required_fields = ["name", "type", "filters"]
        
        for effect_file in effects_dir.glob("*.json"):
            with open(effect_file) as f:
                effect = json.load(f)
            
            for field in required_fields:
                assert field in effect, f"Missing '{field}' in {effect_file.name}"


class TestMasterBus:
    """Test master bus configuration."""

    def test_master_bus_valid(self):
        """Master bus config should be valid if present."""
        from pathlib import Path
        master_bus_path = Path(__file__).parent.parent / "master_bus.json"
        
        if master_bus_path.exists():
            with open(master_bus_path) as f:
                config = json.load(f)
            
            assert "name" in config, "master_bus.json should have 'name' field"

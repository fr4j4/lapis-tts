"""
Tests for the TTS Engine module.

Run with: pytest tests/test_engine.py -v
"""
import pytest
import io
from pathlib import Path


class TestTTSEngine:
    """Test the TTSEngine class."""

    def test_engine_initialization(self):
        """Engine should initialize with voices directory."""
        from src.tts.engine import TTSEngine
        
        voices_dir = Path(__file__).parent.parent / "voices"
        engine = TTSEngine(str(voices_dir))
        
        # Should have a valid voices directory
        assert engine.voices_dir.exists(), "Voices directory should exist"

    def test_load_voice(self):
        """Engine should load a voice model."""
        from src.tts.engine import TTSEngine
        
        voices_dir = Path(__file__).parent.parent / "voices"
        engine = TTSEngine(str(voices_dir))
        
        # Test loading an existing voice
        voice = engine.load_voice("en_US-lessac-high")
        assert voice is not None, "Should load known model"

    def test_synthesize_returns_bytes(self):
        """synthesize() should return bytes (audio data)."""
        from src.tts.engine import TTSEngine
        
        voices_dir = Path(__file__).parent.parent / "voices"
        engine = TTSEngine(str(voices_dir))
        
        audio = engine.synthesize("en_US-lessac-high", "Hello world")
        
        assert isinstance(audio, bytes), "synthesize() should return bytes"
        assert len(audio) > 0, "Audio data should not be empty"

    def test_list_voices(self):
        """list_voices() should list available ONNX files."""
        from src.tts.engine import TTSEngine
        
        voices_dir = Path(__file__).parent.parent / "voices"
        engine = TTSEngine(str(voices_dir))
        
        voices = engine.list_voices()
        assert len(voices) > 0, "Should list at least one voice file"


class TestVoiceConfigManager:
    """Test the VoiceConfigManager class."""

    def test_load_all_configs(self):
        """Should load all voice configs."""
        from src.voice_config.manager import VoiceConfigManager
        
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        manager = VoiceConfigManager(str(configs_dir))
        
        # Should have loaded configs
        assert len(manager._configs) > 0, "Should load at least one voice config"

    def test_list_voices_excludes_inactive(self):
        """list_voices() should exclude inactive voices by default."""
        from src.voice_config.manager import VoiceConfigManager
        
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        manager = VoiceConfigManager(str(configs_dir))
        
        voices = manager.list_voices(include_inactive=False)
        voice_ids = [v["voice_id"] for v in voices]
        
        # Inactive voices should not appear
        assert "robot-en" not in voice_ids, "Inactive voices should be excluded"
        assert "robot-es" not in voice_ids, "Inactive voices should be excluded"

    def test_list_voices_includes_inactive_when_requested(self):
        """list_voices(include_inactive=True) should include inactive voices."""
        from src.voice_config.manager import VoiceConfigManager
        
        configs_dir = Path(__file__).parent.parent / "voice-configs"
        manager = VoiceConfigManager(str(configs_dir))
        
        voices = manager.list_voices(include_inactive=True)
        voice_ids = [v["voice_id"] for v in voices]
        
        # Inactive voices should appear when requested
        assert "robot-en" in voice_ids, "Inactive voices should be included when requested"
        assert "robot-es" in voice_ids, "Inactive voices should be included when requested"


class TestEffectsRegistry:
    """Test the EffectsRegistry class."""

    def test_load_all_effects(self):
        """Should load all effect configurations."""
        from src.effects.registry import EffectsRegistry
        
        effects_dir = Path(__file__).parent.parent / "effects"
        registry = EffectsRegistry(str(effects_dir))
        
        # Should have loaded some effects
        effects = registry.list_effects()
        assert len(effects) > 0, "Should load at least one effect"

    def test_get_effect(self):
        """Should return effect configuration."""
        from src.effects.registry import EffectsRegistry
        
        effects_dir = Path(__file__).parent.parent / "effects"
        registry = EffectsRegistry(str(effects_dir))
        
        effect = registry.get_effect("normal")
        assert effect is not None, "Should return known effect"
        assert "filters" in effect, "Effect should have 'filters'"

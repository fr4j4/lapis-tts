"""
Sistema de efectos de audio extensible.
Interfaz base para todos los procesadores de efectos.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class EffectBase(ABC):
    """Interfaz base para efectos de audio."""

    name: str = "base"
    effect_type: str = "base"

    @abstractmethod
    def apply(self, audio_bytes: bytes, config: Dict[str, Any]) -> bytes:
        """
        Aplicar efecto al audio.

        Args:
            audio_bytes: Audio en formato WAV
            config: Configuración del efecto (filters, params, etc.)

        Returns:
            Audio procesado
        """
        pass

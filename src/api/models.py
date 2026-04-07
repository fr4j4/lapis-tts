"""
Pydantic models for the API.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class VoiceInfo(BaseModel):
    """Information about an available voice."""
    voice_id: str
    name: str
    description: str = ""
    model: str
    modes: List[str] = []


class VoiceList(BaseModel):
    """List of available voices."""
    voices: List[VoiceInfo]


class VoiceDetail(BaseModel):
    """Full configuration details for a voice."""
    voice_id: str
    name: str
    description: str
    model: str
    params: Dict[str, Any]
    modes: Dict[str, Any]
    segment_silence: float
    crossfade: float
    global_effects: List[str]


class TTSRequest(BaseModel):
    """TTS generation request."""
    text: str
    length_scale: Optional[float] = Field(default=None, ge=0.1, le=3.0)
    noise_scale: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    noise_w_scale: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    speaker_id: Optional[int] = None
    output_format: Optional[str] = Field(default="wav", pattern="^(wav|ogg|mp3)$")


class ModelInfo(BaseModel):
    """Information about a model."""
    model_id: str
    name: str
    description: str = ""


class ModelList(BaseModel):
    """List of available models."""
    models: List[ModelInfo]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str = "lapis"
    version: str = "0.2.0"
    available_voices: List[str] = []

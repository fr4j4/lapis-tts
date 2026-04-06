"""
REST endpoints compatible with the ElevenLabs API.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import Response, FileResponse

from src.api.models import (
    VoiceInfo, VoiceList, VoiceDetail, TTSRequest, TTSRequestBody,
    HealthResponse, ModelInfo, ModelList,
)
from src.tts.engine import TTSEngine
from src.voice_config.manager import VoiceConfigManager
from src.effects.registry import EffectsRegistry
from src.effects.pipeline import EffectsPipeline
from src.utils.text import parse_annotated_text, is_annotated
from src.utils.audio import convert_audio_format

logger = logging.getLogger(__name__)

router = APIRouter()

# Global dependencies (initialized in init_router)
tts_engine: TTSEngine = None
voice_config_manager: VoiceConfigManager = None
effects_registry: EffectsRegistry = None
effects_pipeline: EffectsPipeline = None

# Available models for /v1/models endpoints
AVAILABLE_MODELS = [
    ModelInfo(
        model_id="piper",
        name="Piper TTS",
        description="Local Piper neural text-to-speech engine",
    ),
]

# Default voice for POST /v1/text-to-speech (body without voice_id)
DEFAULT_VOICE_ID = "lessac-en"


@router.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon to avoid 404 noise."""
    return Response(status_code=204)


def init_router(engine: TTSEngine, config_mgr: VoiceConfigManager, registry: EffectsRegistry, global_config: dict = None):
    """Initialize the router with dependencies."""
    global tts_engine, voice_config_manager, effects_registry, effects_pipeline
    tts_engine = engine
    voice_config_manager = config_mgr
    effects_registry = registry
    effects_pipeline = EffectsPipeline(registry, global_config)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Server health check."""
    voices = voice_config_manager.list_voices() if voice_config_manager else []
    voice_ids = [v["voice_id"] for v in voices]
    return HealthResponse(status="ok", available_voices=voice_ids)


@router.get("/v1/voices", response_model=VoiceList)
async def list_voices():
    """List available voices (ElevenLabs compatible)."""
    if not voice_config_manager:
        raise HTTPException(status_code=500, detail="Server not initialized")

    voices_data = voice_config_manager.list_voices()
    voices = [VoiceInfo(
        voice_id=v["voice_id"],
        name=v["name"],
        description=v["description"],
        model=v["model"],
        modes=v["modes"],
    ) for v in voices_data]
    return VoiceList(voices=voices)


@router.get("/v1/voices/{voice_id}", response_model=VoiceDetail)
async def get_voice(voice_id: str):
    """Get full configuration details for a voice."""
    if not voice_config_manager:
        raise HTTPException(status_code=500, detail="Server not initialized")

    config = voice_config_manager.get_voice(voice_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

    return VoiceDetail(
        voice_id=voice_id,
        name=config.get("name", voice_id),
        description=config.get("description", ""),
        model=config.get("model", ""),
        params=config.get("params", {}),
        modes=config.get("modes", {}),
        segment_silence=config.get("segment_silence", 0.15),
        crossfade=config.get("crossfade", 0.05),
        global_effects=config.get("global_effects", []),
    )


@router.get("/v1/models", response_model=ModelList)
async def list_models():
    """List available models (ElevenLabs compatible)."""
    return ModelList(models=AVAILABLE_MODELS)


@router.get("/v1/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """Get model details (ElevenLabs compatible)."""
    for model in AVAILABLE_MODELS:
        if model.model_id == model_id:
            return model
    raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


@router.post("/v1/text-to-speech/{voice_id}")
async def text_to_speech(
    voice_id: str,
    request: TTSRequest,
    x_api_key: Optional[str] = Header(None, alias="xi-api-key"),
):
    """
    Generate TTS audio (ElevenLabs compatible).

    The voice_id is resolved to a voice configuration.
    If the voice_id is not configured, returns 404.
    Accepts xi-api-key header but does not validate it.
    """
    # Log if API key provided (for debugging/debug clients)
    if x_api_key:
        logger.debug(f"Received xi-api-key (ignored): {x_api_key[:8]}...")

    return await _tts_generate(voice_id, request)


@router.post("/v1/text-to-speech")
async def text_to_speech_body(
    request: TTSRequestBody,
    x_api_key: Optional[str] = Header(None, alias="xi-api-key"),
):
    """
    Generate TTS audio with voice_id in request body (ElevenLabs compatible).

    Uses DEFAULT_VOICE_ID if voice_id not provided in body.
    Accepts xi-api-key header but does not validate it.
    """
    if x_api_key:
        logger.debug(f"Received xi-api-key (ignored): {x_api_key[:8]}...")

    voice_id = request.voice_id or DEFAULT_VOICE_ID

    # Convert body request to TTSRequest
    tts_request = TTSRequest(
        text=request.text,
        model_id=request.model_id,
        voice_settings=request.voice_settings,
        length_scale=request.length_scale,
        noise_scale=request.noise_scale,
        noise_w_scale=request.noise_w_scale,
        speaker_id=request.speaker_id,
        output_format=request.output_format,
    )

    return await _tts_generate(voice_id, tts_request)


async def _tts_generate(voice_id: str, request: TTSRequest):
    """
    Internal TTS generation function.

    Accepts voice_settings but ignores it (Piper uses different parameters).
    Converts output to wav (default), ogg, or mp3 as requested.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")

    # Resolve voice config
    voice_config = voice_config_manager.get_voice(voice_id)
    if not voice_config:
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found. Use /v1/voices to list available voices."
        )

    voice_model = voice_config["model"]

    # Get parameters from voice config defaults, overridden by request
    config_params = voice_config.get("params", {})
    length_scale = request.length_scale if request.length_scale is not None else config_params.get("length_scale", 1.0)
    noise_scale = request.noise_scale if request.noise_scale is not None else config_params.get("noise_scale", 0.667)
    noise_w = request.noise_w_scale if request.noise_w_scale is not None else config_params.get("noise_w_scale", 0.8)
    output_format = request.output_format or "mp3"

    # Log ignored parameters for debugging
    if request.voice_settings:
        logger.debug(f"voice_settings received (ignored): {request.voice_settings}")

    try:
        # Check if text has annotation tags
        if is_annotated(request.text):
            audio_bytes = await _generate_annotated(
                voice_model,
                request.text,
                length_scale,
                noise_scale,
                noise_w,
                voice_config,
            )
        else:
            # Simple generation
            audio_bytes = tts_engine.synthesize(
                voice_model,
                request.text,
                length_scale=length_scale,
                noise_scale=noise_scale,
                noise_w_scale=noise_w,
            )

            # Apply effects pipeline (normal mode)
            segments = [{"audio": audio_bytes, "mode": "normal"}]
            audio_bytes = effects_pipeline.process_full(segments, voice_config)

        # Convert to requested output format
        audio_bytes = convert_audio_format(audio_bytes, output_format)

        content_types = {"wav": "audio/wav", "ogg": "audio/ogg", "mp3": "audio/mpeg"}
        extensions = {"wav": "wav", "ogg": "ogg", "mp3": "mp3"}
        media_type = content_types.get(output_format, "audio/wav")
        ext = extensions.get(output_format, "wav")

        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="audio.{ext}"',
            },
        )

    except ValueError as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error generating TTS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


async def _generate_annotated(
    voice_model: str,
    text: str,
    length_scale: float,
    noise_scale: float,
    noise_w: float,
    voice_config: dict,
) -> bytes:
    """Generate audio with annotated text (<mode>text</mode> tags)."""
    segments = parse_annotated_text(text)
    available_modes = set(voice_config.get("modes", {}).keys())
    audio_segments = []

    for segment_text, mode in segments:
        # Fallback to "normal" if mode is not available for this voice
        if mode not in available_modes:
            logger.warning(f"Mode '{mode}' not available for voice, falling back to 'normal'")
            mode = "normal"

        audio_bytes = tts_engine.synthesize(
            voice_model,
            segment_text,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w,
        )

        audio_segments.append({"audio": audio_bytes, "mode": mode})

    # Process with pipeline (per-mode effects + global effects)
    return effects_pipeline.process_full(audio_segments, voice_config)

"""
REST endpoints for the LAPIS TTS API.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse

from src.api.models import (
    VoiceInfo, VoiceList, VoiceDetail, TTSRequest,
    HealthResponse,
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
    """List available voices."""
    if not voice_config_manager:
        raise HTTPException(status_code=500, detail="Server not initialized")

    voices_data = voice_config_manager.list_voices()
    voices = [VoiceInfo(
        voice_id=v["voice_id"],
        name=v["name"],
        description=v["description"],
        model=v["model"],
        modes=v.get("modes", []),
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


@router.post("/v1/text-to-speech/{voice_id}")
async def text_to_speech(
    voice_id: str,
    request: TTSRequest,
):
    """
    Generate TTS audio.

    The voice_id is resolved to a voice configuration.
    If the voice_id is not configured, returns 404.
    """
    return await _tts_generate(voice_id, request)


async def _tts_generate(voice_id: str, request: TTSRequest):
    """
    Internal TTS generation function.
    Converts output to wav (default), ogg, or mp3 as requested.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")

    voice_config = voice_config_manager.get_voice(voice_id)
    if not voice_config:
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found. Use /v1/voices to list available voices."
        )

    voice_model = voice_config["model"]

    config_params = voice_config.get("params", {})
    length_scale = request.length_scale if request.length_scale is not None else config_params.get("length_scale", 1.0)
    noise_scale = request.noise_scale if request.noise_scale is not None else config_params.get("noise_scale", 0.667)
    noise_w = request.noise_w_scale if request.noise_w_scale is not None else config_params.get("noise_w_scale", 0.8)
    output_format = request.output_format or "wav"

    try:
        valid_modes = set(voice_config.get("modes", {}).keys()) | {"normal"}

        if is_annotated(request.text):
            audio_bytes = await _generate_annotated(
                voice_model,
                request.text,
                length_scale,
                noise_scale,
                noise_w,
                voice_config,
                valid_modes,
            )
        else:
            audio_bytes = tts_engine.synthesize(
                voice_model,
                request.text,
                length_scale=length_scale,
                noise_scale=noise_scale,
                noise_w_scale=noise_w,
            )

            segments = [{"audio": audio_bytes, "mode": "normal"}]
            audio_bytes = effects_pipeline.process_full(segments, voice_config)

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
    valid_modes: set,
) -> bytes:
    """Generate audio with annotated text (<mode>text</mode> tags)."""
    segments = parse_annotated_text(text, valid_modes)
    audio_segments = []

    for segment_text, mode in segments:
        audio_bytes = tts_engine.synthesize(
            voice_model,
            segment_text,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w,
        )

        audio_segments.append({"audio": audio_bytes, "mode": mode})

    return effects_pipeline.process_full(audio_segments, voice_config)

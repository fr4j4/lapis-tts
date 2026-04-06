"""
LAPIS - Local API for Speech - ElevenLabs-compatible TTS server.
Uses Piper as the speech synthesis engine with in-memory audio processing.
"""
import argparse
import logging
import sys
from pathlib import Path

import json
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import router, init_router
from src.tts.engine import TTSEngine
from src.voice_config.manager import VoiceConfigManager
from src.effects.registry import EffectsRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


def create_app(config_dir: str = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="LAPIS - Local API for Speech",
        description="Local TTS server compatible with ElevenLabs API using Piper",
        version="0.2.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Determine directories
    base_dir = Path(__file__).parent.parent
    if config_dir:
        config_path = Path(config_dir)
    else:
        config_path = base_dir

    voices_dir = config_path / "voices"
    effects_dir = config_path / "effects"
    voice_configs_dir = config_path / "voice-configs"

    # Verify required directories exist
    for dir_name, dir_path in [("voices", voices_dir), ("effects", effects_dir), ("voice-configs", voice_configs_dir)]:
        if not dir_path.exists():
            logger.error(f"Required directory does not exist: {dir_path}")
            sys.exit(1)

    # Load global configuration (master bus)
    master_bus_path = config_path / "master_bus.json"
    if master_bus_path.exists():
        with open(master_bus_path, "r", encoding="utf-8") as f:
            master_config = json.load(f)
        logger.info(f"Master bus config loaded: {master_config.get('name', 'global')}")
    else:
        master_config = {}
        logger.warning("master_bus.json not found, using empty configuration")

    # Initialize components
    logger.info(f"Loading voices from: {voices_dir}")
    engine = TTSEngine(str(voices_dir))

    logger.info(f"Loading voice configs from: {voice_configs_dir}")
    config_manager = VoiceConfigManager(str(voice_configs_dir))

    logger.info(f"Loading effects from: {effects_dir}")
    effects = EffectsRegistry(str(effects_dir))

    # Initialize router with dependencies
    init_router(engine, config_manager, effects, master_config)
    app.include_router(router)

    # Mount static files (playground web UI)
    public_dir = base_dir / "public"
    if public_dir.exists():
        app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

        @app.get("/")
        async def root():
            return FileResponse(public_dir / "index.html")

    # Initialization log
    voices = config_manager.list_voices()
    logger.info(f"Mapped voices: {len(voices)}")
    logger.info(f"Loaded effects: {len(effects.list_effects())}")

    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LAPIS - Local API for Speech Server")
    parser.add_argument("--port", type=int, default=3000, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--config", type=str, default=None, help="Configuration directory")
    args = parser.parse_args()

    app = create_app(args.config)

    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"API documentation: http://{args.host}:{args.port}/docs")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

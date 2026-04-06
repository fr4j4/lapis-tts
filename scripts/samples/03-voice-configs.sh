#!/bin/bash
# Generate voice config examples - one audio per voice config
# Demonstrates each voice with its default parameters and global effects

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
OUTPUT_DIR="$PROJECT_DIR/output"

cd "$PROJECT_DIR"

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Generating voice config examples..."
echo ""

python3 -c "
import sys, json
sys.path.insert(0, '.')
from src.tts.engine import TTSEngine
from src.voice_config.manager import VoiceConfigManager
from src.effects.registry import EffectsRegistry
from src.effects.pipeline import EffectsPipeline

engine = TTSEngine('voices')
config_mgr = VoiceConfigManager('voice-configs')
registry = EffectsRegistry('effects')
pipeline = EffectsPipeline(registry)

for voice_id, config in config_mgr._configs.items():
    print(f'Generating with voice: {voice_id}')
    model = config['model']
    params = config.get('params', {})
    
    engine.load_voice(model)
    
    # Use English or Spanish text based on model
    if 'es_' in model or 'ald' in model:
text = 'Hola, esta es una prueba del servidor TTS local de LAPIS.'
    else
        text = 'Hello, this is a test of the LAPIS TTS local server.'
    
    audio = engine.synthesize(
        model, text,
        length_scale=params.get('length_scale', 1.0),
        noise_scale=params.get('noise_scale', 0.667),
        noise_w_scale=params.get('noise_w_scale', 0.8),
    )
    
    segments = [{'audio': audio, 'mode': 'normal'}]
    processed = pipeline.process_full(segments, config)
    
    filename = f'$OUTPUT_DIR/03-voice-{voice_id}.wav'
    with open(filename, 'wb') as f:
        f.write(processed)
    print(f'   Saved: {len(processed)} bytes')
"

echo ""
echo "Voice config examples generated in $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/03-*.wav 2>/dev/null || echo "No files generated"

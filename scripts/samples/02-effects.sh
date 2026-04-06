#!/bin/bash
# Generate effect examples - one audio per available effect
# Uses the glados-es voice config

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

echo "Generating effect examples..."
echo ""

VOICE="es_ES-glados-medium"

if [ ! -f "voices/$VOICE.onnx" ]; then
    echo "Voice $VOICE not found"
    exit 1
fi

TEXT="This is a test of the audio effects system. Each file demonstrates a different effect."

# List of effects
EFFECTS="normal whisper breathy emphatic radio processed"

for EFFECT in $EFFECTS; do
    echo "Generating with effect: $EFFECT"
    
    FILENAME="02-effect-${EFFECT}.wav"
    
    python3 -c "
import sys, json
sys.path.insert(0, '.')
from src.tts.engine import TTSEngine
from src.voice_config.manager import VoiceConfigManager
from src.effects.registry import EffectsRegistry
from src.effects.pipeline import EffectsPipeline

engine = TTSEngine('voices')
engine.load_voice('$VOICE')

# Load voice config
config_mgr = VoiceConfigManager('voice-configs')
voice_config = config_mgr.get_voice('glados-es')

# Load effects
registry = EffectsRegistry('effects')
pipeline = EffectsPipeline(registry)

# Generate audio
audio = engine.synthesize('$VOICE', '''$TEXT''')

# Apply effect
segments = [{'audio': audio, 'mode': '$EFFECT'}]
processed = pipeline.process_full(segments, voice_config)

with open('$OUTPUT_DIR/$FILENAME', 'wb') as f:
    f.write(processed)
print(f'   Saved: {len(processed)} bytes')
"
done

echo ""
echo "Effect examples generated in $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/02-*.wav 2>/dev/null || echo "No files generated"

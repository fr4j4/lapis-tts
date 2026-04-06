#!/bin/bash
# Generate basic examples - one voice per available model
# No effects, just raw voice

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

echo "Generating basic examples..."
echo ""

# Get list of available voices
VOICES=$(ls voices/*.onnx 2>/dev/null | xargs -n1 basename | sed 's/.onnx//')

if [ -z "$VOICES" ]; then
    echo "No voices found in voices/"
    exit 1
fi

for VOICE in $VOICES; do
    echo "Generating with voice: $VOICE"
    
    # Text in English or Spanish based on voice name
    if [[ "$VOICE" == *"en_"* ]] || [[ "$VOICE" == *"lessac"* ]] || [[ "$VOICE" == "glados" ]]; then
        TEXT="Hello, this is a basic test of the LAPIS TTS local server. Everything is working perfectly."
        FILENAME="01-basic-${VOICE}-en.wav"
    else
        TEXT="Hola, esta es una prueba basica del servidor TTS local de LAPIS. Todo funciona correctamente."
        FILENAME="01-basic-${VOICE}-es.wav"
    fi
    
    # Generate audio
    python3 -c "
import sys
sys.path.insert(0, '.')
from src.tts.engine import TTSEngine

engine = TTSEngine('voices')
engine.load_voice('$VOICE')
audio = engine.synthesize('$VOICE', '''$TEXT''')
with open('$OUTPUT_DIR/$FILENAME', 'wb') as f:
    f.write(audio)
print(f'   Saved: {len(audio)} bytes')
"
done

echo ""
echo "Basic examples generated in $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/01-*.wav 2>/dev/null || echo "No files generated"

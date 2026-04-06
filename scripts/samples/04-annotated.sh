#!/bin/bash
# Generate annotated text examples with <mode>text</mode> tags

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

echo "Generating annotated text examples..."
echo ""

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from src.tts.engine import TTSEngine
from src.voice_config.manager import VoiceConfigManager
from src.effects.registry import EffectsRegistry
from src.effects.pipeline import EffectsPipeline
from src.utils.text import parse_annotated_text

engine = TTSEngine('voices')
config_mgr = VoiceConfigManager('voice-configs')
registry = EffectsRegistry('effects')
pipeline = EffectsPipeline(registry)

# Example 1: English with whisper and emphatic
print("Example 1: English with whisper and emphatic tags")
voice_config = config_mgr.get_voice('pMsXgVXv3BLzUgSXRplE')
model = voice_config['model']
engine.load_voice(model)

text = 'Hello <whisper>can you hear me?</whisper> This is <emphatic>very important</emphatic> information.'
segments = parse_annotated_text(text)
audio_segments = []
for seg_text, mode in segments:
    audio = engine.synthesize(model, seg_text)
    audio_segments.append({'audio': audio, 'mode': mode})

processed = pipeline.process_full(audio_segments, voice_config)
filename = f'{sys.argv[1]}/04-annotated-en-whisper-emphatic.wav'
with open(filename, 'wb') as f:
    f.write(processed)
print(f'   Saved: {len(processed)} bytes')

# Example 2: GLaDOS Spanish with robotic and menacing
print("Example 2: GLaDOS Spanish with robotic and menacing tags")
voice_config = config_mgr.get_voice('glados-es')
model = voice_config['model']
engine.load_voice(model)

text = 'Hello <robotic>attention</robotic> This is <menacing>your final warning</menacing> Comply now.'
segments = parse_annotated_text(text)
audio_segments = []
for seg_text, mode in segments:
    audio = engine.synthesize(model, seg_text)
    audio_segments.append({'audio': audio, 'mode': mode})

processed = pipeline.process_full(audio_segments, voice_config)
filename = f'{sys.argv[1]}/04-annotated-glados-robotic-menacing.wav'
with open(filename, 'wb') as f:
    f.write(processed)
print(f'   Saved: {len(processed)} bytes')

# Example 3: DaveFX narrator with warm and dramatic
print("Example 3: DaveFX narrator with warm and dramatic tags")
voice_config = config_mgr.get_voice('davefx')
model = voice_config['model']
engine.load_voice(model)

text = 'Era una noche <warm>tranquila y serena</warm> cuando de pronto <dramatic>todo cambio para siempre</dramatic> en el silencio.'
segments = parse_annotated_text(text)
audio_segments = []
for seg_text, mode in segments:
    audio = engine.synthesize(model, seg_text)
    audio_segments.append({'audio': audio, 'mode': mode})

processed = pipeline.process_full(audio_segments, voice_config)
filename = f'{sys.argv[1]}/04-annotated-davefx-warm-dramatic.wav'
with open(filename, 'wb') as f:
    f.write(processed)
print(f'   Saved: {len(processed)} bytes')
PYEOF

echo ""
echo "Annotated text examples generated in $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/04-*.wav 2>/dev/null || echo "No files generated"

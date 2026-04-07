#!/bin/bash
# Start script for LAPIS - Local API for Speech

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Run ./scripts/install.sh first"
    exit 1
fi

# Check voices
VOICES_DIR="$PROJECT_DIR/voices"
VOICE_COUNT=$(ls -1 "$VOICES_DIR/"*.onnx 2>/dev/null | wc -l)
if [ "$VOICE_COUNT" -eq 0 ]; then
    echo "No voices found. Run ./scripts/install.sh --download-voices"
    exit 1
fi

echo "Starting LAPIS - Local API for Speech..."
echo "   Voices: $VOICE_COUNT"
echo ""

exec python -m src.main "$@"

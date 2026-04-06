#!/bin/bash
# Start script for LAPIS - Local API for Speech

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activar venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️  Entorno virtual no encontrado. Ejecuta ./scripts/install.sh"
    exit 1
fi

# Verificar voces
VOICES_DIR="$PROJECT_DIR/voices"
VOICE_COUNT=$(ls -1 "$VOICES_DIR/"*.onnx 2>/dev/null | wc -l)
if [ "$VOICE_COUNT" -eq 0 ]; then
    echo "❌ No hay voces. Ejecuta ./scripts/install.sh"
    exit 1
fi

echo "🎙️  Iniciando LAPIS - Local API for Speech..."
echo "   Voces: $VOICE_COUNT"
echo ""

exec python -m src.main "$@"

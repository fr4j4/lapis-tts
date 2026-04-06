#!/bin/bash
# Install script for LAPIS - Local API for Speech
# Instala dependencias Python y descarga voces

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VOICES_DIR="$PROJECT_DIR/voices"

echo "🎙️  Instalando LAPIS - Local API for Speech..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# Crear venv si no existe
if [ ! -d ".venv" ]; then
    echo ""
    echo "🐍 Creando entorno virtual..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencias instaladas"

# Verificar ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg disponible"
else
    echo "⚠️  ffmpeg no disponible (instalar: sudo apt install ffmpeg)"
    echo "   Los efectos de audio no funcionarán sin ffmpeg"
fi

# Descargar voces si no existen
VOICE_COUNT=$(ls -1 "$VOICES_DIR/"*.onnx 2>/dev/null | wc -l)
if [ "$VOICE_COUNT" -eq 0 ]; then
    echo ""
    echo "🎤 Descargando voces..."
    echo "   - en_US-lessac-medium (inglés)"
    echo "   - es_ES-mls_10246-low (español)"
    
    # Descargar desde HuggingFace
    curl -L -o "$VOICES_DIR/en_US-lessac-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    
    curl -L -o "$VOICES_DIR/en_US-lessac-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    
    curl -L -o "$VOICES_DIR/es_ES-mls_10246-low.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx"
    
    curl -L -o "$VOICES_DIR/es_ES-mls_10246-low.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx.json"
    
    echo "✅ Voces descargadas"
else
    echo "✅ Voces incluidas: $VOICE_COUNT"
    ls "$VOICES_DIR/"*.onnx | xargs -n1 basename
fi

echo ""
echo "🚀 Instalación completa!"
echo ""
echo "Ejecuta: ./scripts/start.sh"
echo "O: source .venv/bin/activate && python -m src.main"

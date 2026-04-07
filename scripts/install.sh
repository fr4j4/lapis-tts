#!/bin/bash
# Install script for LAPIS - Local API for Speech
# Installs Python dependencies and downloads voice models

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VOICES_DIR="$PROJECT_DIR/voices"

show_help() {
    cat << 'EOF'
Usage: ./install.sh [options]

Options:
    --download-voices   Download all voices defined in voice-configs/
    --voices-dir DIR     Voices directory (default: ./voices)
    -h, --help           Show this help message

Examples:
    ./install.sh                      # Install dependencies only
    ./install.sh --download-voices   # Install + download all voices
EOF
}

DOWNLOAD_VOICES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --download-voices)
            DOWNLOAD_VOICES=true
            shift
            ;;
        --voices-dir)
            VOICES_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "Installing LAPIS - Local API for Speech..."
echo ""

# Verify Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi
echo "Python: $(python3 --version)"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Dependencies installed"

# Verify ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "ffmpeg available"
else
    echo "Warning: ffmpeg not available (install: sudo apt install ffmpeg)"
    echo "   Audio effects will not work without ffmpeg"
fi

# Function to download a voice from HuggingFace
download_voice() {
    local model="$1"
    local output_dir="$2"
    local onnx_file="${output_dir}/${model}.onnx"
    local json_file="${output_dir}/${model}.onnx.json"

    if [ -f "$onnx_file" ]; then
        echo "   ${model} (already exists)"
        return 0
    fi

    echo "   Downloading ${model}"

    local parts=(${model//-/ })
    local lang="${parts[0]}"
    local region="${parts[1]}"
    local voice="${parts[2]}"
    local quality="${parts[3]}"

    local base_url="https://huggingface.co/rhasspy/piper-voices/resolve/main"
    local onnx_url="${base_url}/${lang}/${region}/${voice}/${quality}/${model}.onnx"
    local json_url="${base_url}/${lang}/${region}/${voice}/${quality}/${model}.onnx.json"

    mkdir -p "$output_dir"

    if curl -L -o "$onnx_file" "$onnx_url" 2>/dev/null; then
        curl -L -o "$json_file" "$json_url" 2>/dev/null || true
        echo "   Downloaded ${model}"
    else
        echo "   Failed to download ${model}"
        rm -f "$onnx_file" "$json_file"
        return 1
    fi
}

# Download voices if none exist or if explicitly requested
VOICE_COUNT=$(ls -1 "$VOICES_DIR/"*.onnx 2>/dev/null | wc -l)
if [ "$VOICE_COUNT" -eq 0 ] || [ "$DOWNLOAD_VOICES" = true ]; then
    if [ "$DOWNLOAD_VOICES" = true ]; then
        echo ""
        echo "Downloading voices from voice-configs/..."
    else
        echo ""
        echo "Downloading voices..."
    fi

    mkdir -p "$VOICES_DIR"

    local failed=0
    for config in "$PROJECT_DIR"/voice-configs/*.json; do
        [ -f "$config" ] || continue
        local model=$(python3 -c "import json; print(json.load(open('$config'))['model'])" 2>/dev/null) || continue
        download_voice "$model" "$VOICES_DIR" || failed=1
    done

    if [ $failed -eq 1 ]; then
        echo ""
        echo "Warning: Some voices failed to download"
    else
        echo ""
        echo "Voices downloaded"
    fi
else
    echo ""
    echo "Voices present: $VOICE_COUNT"
    ls "$VOICES_DIR/"*.onnx | xargs -n1 basename
fi

echo ""
echo "Installation complete!"
echo ""
echo "Run: ./scripts/start.sh"
echo "Or: source .venv/bin/activate && python -m src.main"

# LAPIS - Local API for Speech

A local TTS server using Piper neural text-to-speech engine with in-memory audio processing and customizable voice modes.

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

## Features

- **REST API** — Clean endpoints with annotated text support
- **In-memory processing** — Zero temporary files, everything in RAM
- **11 voice modes** — whisper, robotic, radio, breathy, and more
- **Per-voice configurations** — Unique parameters and effects per voice
- **Annotated text** — `<whisper>text</whisper>` style tags for segment modes
- **Web playground** — Interactive UI at `http://localhost:3000/`

## Quick Start

```bash
# Clone the repo
git clone https://github.com/fr4j4/lapis-tts.git
cd lapis-tts

# Install dependencies
./scripts/install.sh

# Download voice models (optional - only needed voices)
./scripts/install.sh --download-voices

# Start the server
./scripts/start.sh

# Generate speech
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' -o audio.wav
```

## Architecture

```mermaid
flowchart LR
    A["📝 Text Input"] --> B["🔤 Text Parser"]
    B --> C{"Segment<br/>Tags?"}
    C -->|Yes| D["Split by<br/>mode tags"]
    C -->|No| E["Single<br/>normal segment"]
    D --> F["🎤 Piper TTS"]
    E --> F
    F --> G["🎛️ Effects<br/>Pipeline"]
    G --> H["🔊 Master Bus<br/>Normalization"]
    H --> I["📤 Audio<br/>Output"]
    
    style A fill:#e1f5fe
    style F fill:#fff3e0
    style G fill:#f3e5f5
    style I fill:#e8f5e8
```

## Audio Processing Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Piper
    participant Effects
    participant MasterBus
    
    Client->>API: POST /v1/text-to-speech
    API->>API: Parse annotated text
    API->>Piper: Synthesize segment 1
    Piper-->>API: Raw WAV
    API->>Effects: Apply mode effects
    Effects-->>API: Processed audio
    API->>Piper: Synthesize segment 2
    Piper-->>API: Raw WAV
    API->>Effects: Apply mode effects
    Effects-->>API: Processed audio
    API->>MasterBus: Concatenate + normalize
    MasterBus-->>Client: Final audio
```

## Included Voices

| Voice ID | Name | Language | Quality |
|----------|------|----------|---------|
| `lessac-en` | Lessac English | 🇺🇸 English | High |
| `amy-en` | Amy English | 🇺🇸 English | Medium |
| `ryan-en` | Ryan English | 🇺🇸 English | Medium |
| `claude-es` | Claude Spanish | 🇲🇽 Spanish (MX) | High |
| `ald-mx` | Ald Mexican | 🇲🇽 Spanish (MX) | Medium |
| `davefx-es` | DaveFX Narrator | 🇪🇸 Spanish (ES) | Medium |
| `mls-es` | MLS Spanish | 🇪🇸 Spanish (ES) | Low |

## Voice Modes

All voices support 11 modes for changing speech character mid-text:

```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Normal text <whisper>whispered</whisper> <robotic>robotic voice</robotic>"}'
```

| Mode | Description |
|------|-------------|
| `normal` | Default voice |
| `whisper` | Realistic whisper |
| `breathy` | Breathed, intimate |
| `emphatic` | Emphasized clarity |
| `radio` | Intercom/radio effect |
| `processed` | Lab processing |
| `robotic` | Processed + radio |
| `menacing` | Threatening tone |
| `warm` | Cozy delivery |
| `dramatic` | Dramatic emphasis |
| `intimate` | Close, personal |

## Project Structure

```
lapis-tts/
├── voice-configs/          # Voice definitions
│   ├── lessac-en.json
│   └── ...
├── effects/                # Audio effect chains
│   ├── whisper.json
│   └── ...
├── voices/                 # ONNX voice models (downloaded)
├── src/
│   ├── main.py            # FastAPI entry point
│   ├── api/routes.py      # REST endpoints
│   ├── tts/engine.py      # Piper wrapper
│   └── effects/           # Audio processing
├── public/                 # Web playground
├── scripts/
│   ├── install.sh         # Setup + voice download
│   └── start.sh           # Launch server
└── tests/                 # Test suite
```

## Requirements

- **Python 3.9+**
- **ffmpeg** — `sudo apt install ffmpeg` or `brew install ffmpeg`
- **~500MB** disk space for voice models

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/voices` | List all voices |
| `GET` | `/v1/voices/{id}` | Voice details |
| `POST` | `/v1/text-to-speech/{id}` | Generate audio |

### Request Example

```json
{
  "text": "Hello <whisper>world</whisper>",
  "length_scale": 1.0,
  "noise_scale": 0.667
}
```

### Response

Returns audio binary with `Content-Disposition: attachment; filename="audio.wav"`

## LAPIS Integration

```json
{
  "plugins": {
    "entries": {
      "lapis-tts": {
        "enabled": true,
        "config": {
          "baseUrl": "http://localhost:3000",
          "voice": "lessac-en"
        }
      }
    }
  },
  "messages": {
    "tts": {
      "auto": "tagged",
      "provider": "lapis",
      "modelOverrides": {
        "enabled": true
      },
      "providers": {
        "lapis": {
          "enabled": true,
          "baseUrl": "http://localhost:3000",
          "voice": "lessac-en"
        }
      }
    }
  }
}
```

## License

MIT License - see [LICENSE](LICENSE)

## Voice Licenses

All included voices are MIT or Public Domain licensed. See [VOICES_LICENSE.md](VOICES_LICENSE.md) for details.

## Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| Piper | MIT | TTS engine |
| FastAPI | MIT | Web framework |
| ffmpeg | LGPL | Audio effects |
| numpy | BSD | Audio processing |

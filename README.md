# LAPIS - Local API for Speech

A local TTS server using Piper neural text-to-speech engine with in-memory audio processing and customizable voice modes.

## Why Lapis TTS?

I wanted to give voice to my AI assistant. I tried services like ElevenLabs, which had great voices, but the tokens ran out too fast. So I discovered Piper TTS and other local technologies, and decided to create a service to have that voice I wanted - unlimited, completely free, and local.

OpenClaw can install and auto-configure the server simply by providing the repository URL.

---

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
- **Benchmark suite** — Test performance, latency, and resource usage at `/benchmark.html`

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
- **pip packages** — see `requirements.txt`

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

### Benchmark Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/benchmark/system` | System information (CPU, RAM, etc.) |
| `POST` | `/v1/benchmark/run` | Run a benchmark test |
| `GET` | `/v1/benchmark/history` | List benchmark history |
| `GET` | `/v1/benchmark/{test_id}` | Get detailed benchmark results |
| `DELETE` | `/v1/benchmark/{test_id}` | Delete a benchmark result |
| `GET` | `/v1/benchmark/export/{test_id}` | Export results as CSV |

#### Run Benchmark

```bash
curl -X POST http://localhost:3000/v1/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, this is a test.",
    "voices": ["lessac-en", "amy-en"],
    "repetitions": 1
  }'
```

**Request Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | "Hello world..." | Text to synthesize |
| `voices` | array | all voices | List of voice IDs to test |
| `repetitions` | int | 1 | Number of repetitions (1-10) |

**Response:**

```json
{
  "test_id": "b4b5319c",
  "timestamp": "2026-04-08T19:31:37.338490",
  "aggregate": {
    "total_tests": 7,
    "successful": 7,
    "failed": 0,
    "avg_latency_ms": 927.77,
    "avg_synthesis_time_ms": 927.77,
    "avg_audio_size_bytes": 82622.29,
    "avg_chars_per_second": 17.6,
    "min_latency_ms": 784.82,
    "max_latency_ms": 1220.51
  },
  "system_info": {
    "cpu_cores": 8,
    "ram_total_gb": 31.25,
    "process_memory_mb": 73.66
  }
}
```

#### Benchmark Metrics

Each benchmark records per-voice metrics:

| Metric | Description |
|--------|-------------|
| `latency_ms` | Total time from request to response |
| `synthesis_time_ms` | Time for Piper synthesis only |
| `audio_size_bytes` | Size of generated audio |
| `audio_duration_ms` | Duration of audio in milliseconds |
| `chars_per_second` | Throughput (characters processed per second) |
| `success` | Whether synthesis succeeded |

#### Benchmark Results

Results are saved to `benchmark-results/benchmark_{test_id}.json` and can be:
- Viewed in the web UI at `/benchmark.html`
- Exported as CSV via `/v1/benchmark/export/{test_id}`
- Compared over time to track performance improvements

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

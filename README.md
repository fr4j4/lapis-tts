# LAPIS - Local API for Speech

A local TTS server compatible with the ElevenLabs API, using [Piper](https://github.com/rhasspy/piper) as the speech synthesis engine with in-memory audio processing and JSON-configurable effects.

## Features

- **ElevenLabs-compatible API** — Drop-in replacement for LAPIS and other ElevenLabs clients
- **In-memory processing** — No temporary files, everything happens in RAM
- **Annotated text** — Change voice mode per segment with `<whisper>text</whisper>` tags
- **JSON-defined effects** — Extensible audio effects processed with ffmpeg
- **Per-voice configuration** — Each voice has its own config with unique modes, parameters, and global effects
- **Fast and local** — No external services, no network latency
- **Web playground** — Interactive UI for testing voices and modes

## Architecture

The system uses a 4-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  1. VOICES (voices/)                                        │
│     ONNX models — the raw voice synthesis engine            │
│     - en_US-lessac-high.onnx                               │
│     - es_MX-claude-high.onnx                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. VOICE CONFIGS (voice-configs/)                          │
│     Per-voice JSON: model, params, modes, global_effects    │
│     - lessac-en.json → high quality English voice            │
│     - claude-es.json → high quality Spanish (MX) voice       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. EFFECTS (effects/)                                      │
│     ffmpeg filter chains — modify the audio                 │
│     - whisper.json  → [highpass, treble, reverb, ...]       │
│     - radio.json    → [bandpass, compression, ...]          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. AUDIO PIPELINE                                          │
│     Text → Piper → Raw audio → Mode effects → Global FX    │
│     → Master bus → Final WAV                                │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Python 3.9+**
- **pip** (Python package manager)
- **ffmpeg** (for audio effects processing)
- **Piper TTS** (installed via the install script)

## Installation

```bash
cd lapis
chmod +x scripts/install.sh
./scripts/install.sh
```

The install script:
1. Creates a Python virtual environment
2. Installs all dependencies
3. Downloads voice models (English and Spanish)
4. Verifies ffmpeg is available

## Start the Server

```bash
./scripts/start.sh
# Or with custom options
./scripts/start.sh --port 8080 --host 0.0.0.0
```

The server starts at `http://localhost:3000` by default.

## Verify It Works

```bash
# Health check
curl http://localhost:3000/health

# List available voices
curl http://localhost:3000/v1/voices

# Get voice details
curl http://localhost:3000/v1/voices/lessac-en
```

## Quick Start

### Generate Audio

```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the local TTS server."}' \
  -o audio.wav
```

### Annotated Text with Mode Tags

```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello <whisper>can you hear me?</whisper> This is <emphatic>very important</emphatic>."}' \
  -o audio-annotated.wav
```

### Available Modes

All voices support the same 11 modes:

| Mode | Description |
|------|-------------|
| `normal` | Default voice with body and natural ambiance |
| `whisper` | Realistic whisper |
| `breathy` | Breathed, intimate voice |
| `emphatic` | Emphasis and clarity |
| `radio` | Intercom/radio effect |
| `processed` | Lab/radio processing effect |
| `robotic` | Robotic, mechanical tone (`processed` + `radio`) |
| `menacing` | Threatening, intense tone (`emphatic` + `processed`) |
| `warm` | Warm, cozy delivery (`breathy` + `normal`) |
| `dramatic` | Dramatic emphasis (`emphatic` + `processed`) |
| `intimate` | Close, personal delivery (`whisper` + `breathy`) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `GET` | `/v1/voices` | List available voices |
| `GET` | `/v1/voices/{voice_id}` | Get full voice configuration |
| `POST` | `/v1/text-to-speech/{voice_id}` | Generate TTS audio |

### TTS Request Body

```json
{
  "text": "Text to synthesize",
  "length_scale": 1.0,
  "noise_scale": 0.667,
  "noise_w_scale": 0.8
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | (required) | Text to synthesize (supports `<mode>` tags) |
| `length_scale` | float | from voice config | Speech speed (0.1–3.0) |
| `noise_scale` | float | from voice config | Voice variation (0.0–1.0) |
| `noise_w_scale` | float | from voice config | Phoneme width noise (0.0–1.0) |

## Voice Configuration

Each voice is defined by a JSON file in `voice-configs/`. The config includes the Piper model, synthesis parameters, available modes, and global effects.

See [docs/VOICE_CONFIG.md](docs/VOICE_CONFIG.md) for the full guide.

### Included Voices

This project includes 7 active voices (MIT licensed):

| Voice ID | Name | Language | Model | Quality |
|----------|------|----------|-------|---------|
| `amy-en` | Amy English | 🇺🇸 English | `en_US-amy-medium` | Medium |
| `lessac-en` | Lessac English | 🇺🇸 English | `en_US-lessac-high` | High |
| `ryan-en` | Ryan English | 🇺🇸 English | `en_US-ryan-medium` | Medium |
| `claude-es` | Claude Spanish | 🇲🇽 Spanish (MX) | `es_MX-claude-high` | High |
| `ald-mx` | Ald Mexican | 🇲🇽 Spanish (MX) | `es_MX-ald-medium` | Medium |
| `davefx-es` | DaveFX Narrator | 🇪🇸 Spanish (ES) | `es_ES-davefx-medium` | Medium |
| `mls-es` | MLS Spanish | 🇪🇸 Spanish (ES) | `es_ES-mls_9972-low` | Low |

### Inactive Voices

These voices are configured but disabled (`active: false`):

| Voice ID | Reason |
|----------|--------|
| `robot-en`, `robot-es` | Disabled for testing purposes |

See [VOICES_LICENSE.md](VOICES_LICENSE.md) for full licensing details.

### Example Voice Config

```json
{
  "voice_id": "lessac-en",
  "name": "Lessac English",
  "description": "High-quality English voice.",
  "model": "en_US-lessac-high",
  "active": true,
  "params": {
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w_scale": 0.8
  },
  "segment_silence": 0.0,
  "crossfade": 0.03,
  "global_effects": [],
  "modes": {
    "normal":   { "effects": ["normal"] },
    "whisper":  { "effects": ["whisper"] },
    "robotic":  { "effects": ["processed", "radio"] },
    "menacing": { "effects": ["emphatic", "processed"] }
  }
}
```

## Effects System

Effects are JSON-defined ffmpeg filter chains. Each voice mode references effects by name.

See [docs/EFFECTS.md](docs/EFFECTS.md) for the full guide.

### Adding a New Effect

Create `effects/my_effect.json`:

```json
{
  "name": "my_effect",
  "description": "My custom effect",
  "type": "ffmpeg",
  "filters": [
    "bass=g=3:f=200",
    "treble=g=-2:f=5000",
    "aecho=0.8:0.9:40:0.3"
  ]
}
```

The server loads it automatically on restart.

## Global Effects

Each voice can define `global_effects` — a chain of effects applied to the **complete audio** after all segments are processed. This gives each voice a consistent character.

```json
"global_effects": ["processed"]
```

Processing order:
1. Each segment → mode effects → normalization
2. Concatenate all segments
3. **Voice global_effects** (if configured)
4. **Master bus** (always applied)

## Master Bus

The `master_bus.json` file defines effects applied to all generated audio, regardless of voice:

```json
{
  "name": "master_bus",
  "enabled": true,
  "filters": [
    "acompressor=threshold=-24dB:ratio=4:attack=20:release=80",
    "acompressor=threshold=-18dB:ratio=3:attack=30:release=100",
    "alimiter=limit=-1.5dB:attack=5:release=50",
    "volume=+6dB"
  ],
  "normalization": {
    "target_lufs": -16.0,
    "min_gain": -6.0,
    "max_gain": 18.0
  }
}
```

## LAPIS Integration

In your LAPIS configuration (`~/.lapis/lapis.json`):

```json
{
  "messages": {
    "tts": {
      "provider": "elevenlabs",
      "providers": {
        "elevenlabs": {
          "enabled": true,
          "baseUrl": "http://localhost:3000",
          "apiKey": "dummy",
          "voiceId": "lessac-en"
        }
      }
    }
  }
}
```

## Project Structure

```
lapis/
├── voice-configs/            # Per-voice JSON configurations
│   ├── lessac-en.json
│   ├── claude-es.json
│   ├── davefx-es.json
│   ├── amy-en.json
│   ├── ryan-en.json
│   ├── ald-mx.json
│   ├── mls-es.json
│   └── robot-en.json         # inactive (for testing)
├── effects/                  # Effect definitions (JSON)
│   ├── normal.json
│   ├── whisper.json
│   ├── breathy.json
│   ├── emphatic.json
│   ├── radio.json
│   └── processed.json
├── voices/                   # Piper ONNX models
├── master_bus.json           # Global audio processing
├── public/
│   └── index.html            # Web playground
├── scripts/
│   ├── install.sh            # Installation script
│   └── start.sh              # Server start script
├── src/
│   ├── main.py               # Entry point (FastAPI)
│   ├── api/
│   │   ├── routes.py         # REST endpoints
│   │   └── models.py         # Pydantic models
│   ├── tts/
│   │   └── engine.py         # Piper synthesis engine
│   ├── voice_config/
│   │   └── manager.py        # Voice config loader & validator
│   ├── effects/
│   │   ├── base.py           # Abstract effect base
│   │   ├── ffmpeg.py         # FFmpeg effect processor
│   │   ├── registry.py        # Effect registry
│   │   └── pipeline.py        # Audio effects pipeline
│   └── utils/
│       ├── audio.py           # In-memory audio utilities
│       └── text.py            # Tag parser (<mode>text</mode>)
├── docs/
│   ├── VOICE_CONFIG.md        # Voice configuration guide
│   ├── EFFECTS.md             # Effects system guide
│   └── API.md                 # API reference
├── tests/                    # Test suite
├── requirements.txt
└── README.md
```

## How Audio Processing Works

### Full Flow

```
POST /v1/text-to-speech/lessac-en
     body: {"text": "Hello <whisper>secret</whisper> world"}

  │
  ▼
1. Load voice config for "lessac-en"
   → model: en_US-lessac-high
   → modes: normal, whisper, robotic, menacing
   → global_effects: []
   │
   ▼
2. Parse text → [("Hello ", "normal"), ("secret", "whisper"), (" world", "normal")]
   │
   ▼
3. For each segment:
   a. Piper generates raw audio (in memory)
   b. Look up mode in voice config → effect chain
   c. Apply effect chain with ffmpeg
   d. Dynamic LUFS-based normalization
   e. Add silence padding
   │
   ▼
4. Concatenate all segments
   │
   ▼
5. Apply voice global_effects (if configured)
   │
   ▼
6. Apply master bus (compression, limiting, volume)
   │
   ▼
7. Return audio/wav in HTTP response body
```

## Project Structure

```
lapis/
├── voice-configs/            # Per-voice JSON configurations
│   ├── lessac-en.json
│   ├── claude-es.json
│   ├── davefx-es.json
│   ├── amy-en.json
│   ├── ryan-en.json
│   ├── ald-mx.json
│   ├── mls-es.json
│   └── robot-en.json         # inactive (for testing)
├── effects/                  # Effect definitions (JSON)
│   ├── normal.json
│   ├── whisper.json
│   ├── breathy.json
│   ├── emphatic.json
│   ├── radio.json
│   └── processed.json
├── voices/                   # Piper ONNX models
├── master_bus.json           # Global audio processing
├── public/
│   └── index.html            # Web playground
├── scripts/
│   ├── install.sh            # Installation script
│   └── start.sh              # Server start script
├── src/
│   ├── main.py               # Entry point (FastAPI)
│   ├── api/
│   │   ├── routes.py         # REST endpoints
│   │   └── models.py         # Pydantic models
│   ├── tts/
│   │   └── engine.py         # Piper synthesis engine
│   ├── voice_config/
│   │   └── manager.py        # Voice config loader & validator
│   ├── effects/
│   │   ├── base.py           # Abstract effect base
│   │   ├── ffmpeg.py         # FFmpeg effect processor
│   │   ├── registry.py       # Effect registry
│   │   └── pipeline.py       # Audio effects pipeline
│   └── utils/
│       ├── audio.py          # In-memory audio utilities
│       └── text.py           # Tag parser (<mode>text</mode>)
├── docs/
│   ├── VOICE_CONFIG.md       # Voice configuration guide
│   ├── EFFECTS.md            # Effects system guide
│   └── API.md                # API reference
├── requirements.txt
└── README.md
```

## How Audio Processing Works

### Full Flow

```
POST /v1/text-to-speech/lessac-en
     body: {"text": "Hello <whisper>secret</whisper> world"}

  │
  ▼
1. Load voice config for "lessac-en"
   → model: en_US-lessac-high
   → modes: normal, whisper, robotic, menacing
   → global_effects: []
   │
   ▼
2. Parse text → [("Hello ", "normal"), ("secret", "whisper"), (" world", "normal")]
   │
   ▼
3. For each segment:
   a. Piper generates raw audio (in memory)
   b. Look up mode in voice config → effect chain
   c. Apply effect chain with ffmpeg
   d. Dynamic LUFS-based normalization
   e. Add silence padding
   │
   ▼
4. Concatenate all segments
   │
   ▼
5. Apply voice global_effects: ["processed"]
   │
   ▼
6. Apply master bus (compression, limiting, volume)
   │
   ▼
7. Return audio/wav in HTTP response body
```

### In-Memory Processing

**No temporary files are used.** All processing happens in RAM:

- Piper generates WAV `bytes` directly to `io.BytesIO()`
- ffmpeg reads/writes via stdin/stdout (`pipe:0`, `pipe:1`)
- numpy concatenates arrays in memory
- HTTP response contains WAV bytes directly

## Troubleshooting

### "Voice not found"
Make sure the voice config JSON exists in `voice-configs/` and the `voice_id` matches.

### "ffmpeg not available"
Install ffmpeg: `sudo apt install ffmpeg` (Ubuntu/Debian) or `brew install ffmpeg` (macOS).

### "Model not found"
Ensure the ONNX model file exists in `voices/` and the `model` field in the voice config matches the filename (without `.onnx`).

### Audio sounds wrong
Check the voice config `params` and the effects chain. Use the playground to test different parameters.

## License

MIT

## Dependencies

| Dependency | License | Usage |
|------------|---------|-------|
| **piper-tts** | MIT | Speech synthesis engine |
| **FastAPI** | MIT | Web framework |
| **ffmpeg** | LGPL | Audio effects processing (external CLI) |
| **numpy** | BSD | In-memory audio manipulation |

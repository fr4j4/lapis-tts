# API Reference

LAPIS (Local API for Speech) exposes a REST API compatible with ElevenLabs. All responses include CORS headers.

## Base URL

```
http://localhost:3000
```

## Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "lapis",
  "version": "0.2.0",
  "available_voices": ["lessac-en", "amy-en", "ryan-en", "claude-es", "ald-mx", "davefx-es", "mls-es"]
}
```

### List Voices

```
GET /v1/voices
```

**Response:**
```json
{
  "voices": [
    {
      "voice_id": "lessac-en",
      "name": "Lessac English",
      "description": "High-quality English voice (Lessac). Male, clear, and professional.",
      "model": "en_US-lessac-high",
      "modes": ["normal", "whisper", "breathy", "robotic", "menacing"],
      "preview_url": null,
      "category": "premade"
    }
  ]
}
```

### Get Voice Details

```
GET /v1/voices/{voice_id}
```

**Response:**
```json
{
  "voice_id": "lessac-en",
  "name": "Lessac English",
  "description": "High-quality English voice (Lessac). Male, clear, and professional.",
  "model": "en_US-lessac-high",
  "params": {
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w_scale": 0.8
  },
  "modes": {
    "normal":   { "effects": ["normal"] },
    "whisper":  { "effects": ["whisper"] },
    "robotic":  { "effects": ["processed", "radio"] },
    "menacing": { "effects": ["emphatic", "processed"] }
  },
  "segment_silence": 0.0,
  "crossfade": 0.03,
  "global_effects": []
}
```

### Generate TTS

```
POST /v1/text-to-speech/{voice_id}
```

**Request Body:**
```json
{
  "text": "Hello <whisper>world</whisper>",
  "length_scale": 1.0,
  "noise_scale": 0.667,
  "noise_w_scale": 0.8
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | required | Text to synthesize. Supports `<mode>text</mode>` tags. |
| `length_scale` | float | from voice config | Speech speed (0.1–3.0). |
| `noise_scale` | float | from voice config | Speaker variation (0.0–1.0). |
| `noise_w_scale` | float | from voice config | Phoneme width noise (0.0–1.0). |
| `model_id` | string | ignored | Reserved for future use. |
| `output_format` | string | `mp3` | Output audio format: `wav`, `ogg`, or `mp3`. |

**Response:** `audio/wav`, `audio/ogg`, or `audio/mpeg` binary (according to `output_format`)

**Error Responses:**
- `400` — No text provided or invalid parameters
- `404` — Voice not found
- `500` — Internal server error

### cURL Examples

**Simple generation:**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  -o audio.wav
```

**Annotated text:**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello <whisper>secret</whisper> <robotic>attention</robotic>"}' \
  -o audio.wav
```

**Spanish text:**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/claude-es \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo"}' \
  -o audio.wav
```

**MP3 output (default):**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  -o audio.mp3
```

**OGG output:**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "output_format": "ogg"}' \
  -o audio.ogg
```

**WAV output:**
```bash
curl -X POST http://localhost:3000/v1/text-to-speech/lessac-en \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "output_format": "wav"}' \
  -o audio.wav
```

## Annotated Text Format

Use XML-style tags to change voice mode per segment:

```
Hello <whisper>this is secret</whisper> and <emphatic>listen carefully</emphatic>.
```

### Available Modes

All voices support the same 11 modes. Each mode maps to a chain of ffmpeg audio effects:

| Mode | Effect Chain | Description |
|------|-------------|-------------|
| `normal` | `normal` | Default voice with body and natural ambiance |
| `whisper` | `whisper` | Whispered speech |
| `breathy` | `breathy` | Breathed, intimate voice |
| `emphatic` | `emphatic` | Emphasized, clear speech |
| `radio` | `radio` | Radio/intercom effect |
| `processed` | `processed` | Processed/lab effect |
| `robotic` | `processed` + `radio` | Robotic, mechanical tone |
| `menacing` | `emphatic` + `processed` | Threatening, intense tone |
| `warm` | `breathy` + `normal` | Warm, cozy delivery |
| `dramatic` | `emphatic` + `processed` | Dramatic emphasis |
| `intimate` | `whisper` + `breathy` | Close, personal delivery |

Text outside tags uses the `normal` mode.

## Best Practices for Annotated Text

For the smoothest transitions between segments:
- **Use longer text blocks** (preferably complete sentences or paragraphs)
- Piper synthesizes each block independently and adds its own ending inflection
- Longer blocks = less noticeable transitions
- Avoid very short words (e.g., `<whisper>a</whisper>`) as standalone segments

### Example: Fluid Voice
```json
{
  "voice_id": "davefx-es",
  "segment_silence": 0.08,
  "crossfade": 0.03
}
```
```text
<normal>This is the first complete sentence that flows naturally into the next one.</normal><whisper>And this is a whispered secret that continues the thought seamlessly.</whisper>
```

### Example: Robotic Voice
```json
{
  "voice_id": "lessac-en",
  "segment_silence": 0.2,
  "crossfade": 0
}
```
```text
<normal>System initialization complete.</normal><robotic>All protocols have been verified.</robotic>
```

## ElevenLabs Compatibility

This server is designed as a drop-in replacement for ElevenLabs:

| Feature | Status |
|---------|--------|
| `POST /v1/text-to-speech/{voice_id}` | Compatible |
| `GET /v1/voices` | Compatible (extra fields added) |
| `GET /v1/voices/{voice_id}` | Compatible (extra fields added) |
| Response format (`audio/wav`) | Compatible |
| `model_id` parameter | Accepted, ignored |
| `voice_settings` in body | Not implemented |

Clients that only use `voice_id` and `text` will work without modification.

## Playground

A web-based playground is available at `http://localhost:3000/` for testing voices, modes, and parameters interactively.

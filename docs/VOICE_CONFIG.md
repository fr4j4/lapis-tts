# Voice Configuration Guide

Each voice in LAPIS (Local API for Speech) is defined by a single JSON file in the `voice-configs/` directory. This file contains everything needed: the Piper model, synthesis parameters, available modes, and global effects.

## File Location

```
voice-configs/{voice_id}.json
```

The filename should match the `voice_id` field inside the JSON.

## JSON Schema

```json
{
  "voice_id": "string (required) — Unique identifier, matches ElevenLabs voice_id",
  "name": "string (required) — Human-readable name",
  "description": "string (optional) — Description shown in the playground",
  "model": "string (required) — Piper ONNX model name (without .onnx extension)",
  "params": {
    "length_scale": "number (required) — Speech speed (0.1–3.0, default 1.0)",
    "noise_scale": "number (required) — Speaker variation (0.0–1.0, default 0.667)",
    "noise_w_scale": "number (required) — Phoneme width noise (0.0–1.0, default 0.8)"
  },
  "segment_silence": "number (optional) — Seconds of silence between annotated segments (default 0.15)",
  "crossfade": "number (optional) — Crossfade duration in seconds between segments (default 0.05)",
  "global_effects": ["string (optional) — List of effect names applied to the complete audio"],
  "modes": {
    "mode_name": {
      "effects": ["string — List of effect names from the effects/ directory"]
    }
  }
}
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `voice_id` | string | Unique identifier. Must match the filename. |
| `name` | string | Display name for the UI and API. |
| `model` | string | Piper ONNX model name (e.g., `en_US-lessac-high`). The `.onnx` extension is added automatically. |
| `params` | object | Piper synthesis parameters. Must contain all three: `length_scale`, `noise_scale`, `noise_w_scale`. |
| `modes` | object | At least one mode. Each mode maps to a chain of effects. |

## Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | `""` | Shown in the playground and API. |
| `segment_silence` | number | `0.15` | Silence padding between segments in annotated text. Set to `0` for continuous flow. |
| `crossfade` | number | `0.05` | Crossfade duration in seconds (50ms) between segments for smoother transitions. Set to `0` for robotic voices. |
| `global_effects` | array | `[]` | Effects applied to the complete audio after all segments are concatenated. |

## Modes

All voices support the same 11 modes. Each mode references effects by name from the `effects/` directory:

| Mode | Effect Chain | Description |
|------|-------------|-------------|
| `normal` | `normal` | Default voice |
| `whisper` | `whisper` | Whispered speech |
| `breathy` | `breathy` | Breathed, intimate voice |
| `emphatic` | `emphatic` | Emphasized, clear speech |
| `radio` | `radio` | Radio/intercom effect |
| `processed` | `processed` | Lab/radio processing |
| `robotic` | `processed`, `radio` | Robotic, mechanical tone |
| `menacing` | `emphatic`, `processed` | Threatening, intense tone |
| `warm` | `breathy`, `normal` | Warm, cozy delivery |
| `dramatic` | `emphatic`, `processed` | Dramatic emphasis |
| `intimate` | `whisper`, `breathy` | Close, personal delivery |

```json
"modes": {
  "normal":   { "effects": ["normal"] },
  "whisper":  { "effects": ["whisper"] },
  "robotic":  { "effects": ["processed", "radio"] },
  "menacing": { "effects": ["emphatic", "processed"] }
}
```

When a user writes `<whisper>secret</whisper>`, the system:
1. Finds the `whisper` mode in the voice config
2. Applies each effect in the `effects` chain in order
3. Normalizes the segment volume

## Annotated Text (Segment Modes)

You can use mode tags in the text to change voice characteristics mid-speech:

```text
<whisper>This is a secret</whisper><normal>But this is normal</normal><emphatic>This is emphasized!</emphatic>
```

### Best Practices for Text Segmentation

**For smoother transitions:**
- Use **longer text blocks** (preferably complete sentences or paragraphs)
- Piper synthesizes each block independently and adds its own ending inflection
- Longer blocks = less noticeable transitions
- For fluid voices, use `segment_silence: 0` or low values (0.05-0.08)
- For robotic voices, use higher `segment_silence` (0.15-0.2) to emphasize the pause

**Example for fluid voice:**
```json
{
  "segment_silence": 0.0,
  "crossfade": 0.03
}
```

**Example for robotic voice:**
```json
{
  "segment_silence": 0.2,
  "crossfade": 0
}
```

## Global Effects

`global_effects` are applied to the **complete concatenated audio**, after all segments have been processed individually. This gives each voice a consistent character regardless of which modes are used in the text.

```json
"global_effects": ["processed"]
```

Processing order:
1. Each segment → mode effects → normalization
2. All segments concatenated
3. **Voice global_effects** (if any)
4. **Master bus** (always applied)

### When to Use Global Effects

- **Robotic voices**: Add `processed` or `radio` for a consistent metallic character
- **Narrator voices**: Add `breathy` or `normal` for warmth
- **Clean voices**: Leave empty `[]`

## Examples

### Robotic Voice

```json
{
  "voice_id": "robot-en",
  "name": "Robot English",
  "description": "Robotic, synthetic voice in English.",
  "model": "en_US-ryan-medium",
  "params": {
    "length_scale": 0.95,
    "noise_scale": 0.5,
    "noise_w_scale": 0.6
  },
  "segment_silence": 0.2,
  "crossfade": 0,
  "global_effects": ["processed"],
  "modes": {
    "normal":    { "effects": ["normal"] },
    "whisper":   { "effects": ["whisper"] },
    "breathy":   { "effects": ["breathy"] },
    "emphatic":  { "effects": ["emphatic"] },
    "radio":     { "effects": ["radio"] },
    "processed": { "effects": ["processed"] },
    "robotic":   { "effects": ["processed", "radio"] },
    "menacing":  { "effects": ["emphatic", "processed"] },
    "warm":      { "effects": ["breathy", "normal"] },
    "dramatic":  { "effects": ["emphatic", "processed"] },
    "intimate":  { "effects": ["whisper", "breathy"] }
  }
}
```

### Warm Narrator

```json
{
  "voice_id": "davefx-es",
  "name": "DaveFX Narrator",
  "description": "Deep Spanish narrator voice.",
  "model": "es_ES-davefx-medium",
  "params": {
    "length_scale": 0.9,
    "noise_scale": 0.6,
    "noise_w_scale": 0.7
  },
  "segment_silence": 0.08,
  "crossfade": 0.03,
  "global_effects": [],
  "modes": {
    "normal":    { "effects": ["normal"] },
    "whisper":   { "effects": ["whisper"] },
    "breathy":   { "effects": ["breathy"] },
    "emphatic":  { "effects": ["emphatic"] },
    "radio":     { "effects": ["radio"] },
    "processed": { "effects": ["processed"] },
    "robotic":   { "effects": ["processed", "radio"] },
    "menacing":  { "effects": ["emphatic", "processed"] },
    "warm":      { "effects": ["breathy", "normal"] },
    "dramatic":  { "effects": ["emphatic", "processed"] },
    "intimate":  { "effects": ["whisper", "breathy"] }
  }
}
```

## Adding a New Voice

1. **Download the ONNX model** into the `voices/` directory:
   ```bash
   curl -L -o voices/my_voice.onnx "https://huggingface.co/..."
   curl -L -o voices/my_voice.onnx.json "https://huggingface.co/..."
   ```

2. **Create the voice config** in `voice-configs/my_voice.json`:
   ```json
   {
     "voice_id": "my-voice",
     "name": "My Voice",
     "description": "Description here.",
     "model": "my_voice",
     "params": {
       "length_scale": 1.0,
       "noise_scale": 0.667,
       "noise_w_scale": 0.8
     },
     "segment_silence": 0.08,
     "crossfade": 0.03,
     "global_effects": [],
     "modes": {
       "normal":    { "effects": ["normal"] },
       "whisper":   { "effects": ["whisper"] },
       "breathy":   { "effects": ["breathy"] },
       "emphatic":  { "effects": ["emphatic"] },
       "radio":     { "effects": ["radio"] },
       "processed": { "effects": ["processed"] },
       "robotic":   { "effects": ["processed", "radio"] },
       "menacing":  { "effects": ["emphatic", "processed"] },
       "warm":      { "effects": ["breathy", "normal"] },
       "dramatic":  { "effects": ["emphatic", "processed"] },
       "intimate":  { "effects": ["whisper", "breathy"] }
     }
   }
   ```

3. **Restart the server**. The voice will be loaded automatically.

## Validation

The server validates each voice config on startup. Invalid configs are skipped with an error log. Validation checks:

- All required fields are present
- `params` contains all three numeric values
- `modes` is non-empty and each mode has an `effects` list
- `global_effects` is a list (if present)
- `segment_silence` is numeric (if present)

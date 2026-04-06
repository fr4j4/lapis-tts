# Effects System Guide

LAPIS (Local API for Speech) uses a JSON-defined effects system. Effects are chains of ffmpeg audio filters that modify the synthesized speech.

## Architecture

```
effects/           ← JSON definitions (what effects exist)
  ├── normal.json
  ├── whisper.json
  └── ...

src/effects/       ← Python processors (how effects are applied)
  ├── base.py      ← Abstract base class
  ├── ffmpeg.py    ← FFmpeg processor (current)
  ├── registry.py  ← Loads effects from JSON
  └── pipeline.py  ← Orchestrates effect chains
```

## Effect Definition

Each effect is a JSON file in the `effects/` directory:

```json
{
  "name": "whisper",
  "description": "Realistic whisper with intimate ambiance",
  "type": "ffmpeg",
  "filters": [
    "highpass=f=600",
    "treble=g=6:f=2500",
    "bass=g=-8:f=200",
    "aecho=0.7:0.8:25:0.15",
    "loudnorm=I=-16:TP=-1.5:LRA=11"
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier. Must match the filename stem. |
| `description` | string | Human-readable description. |
| `type` | string | Processor type. Currently only `"ffmpeg"` is supported. |
| `filters` | array | List of ffmpeg audio filter strings. Applied in order. |

## Available Effects

| Effect | Description | Key Filters |
|--------|-------------|-------------|
| `normal` | Base voice with body and natural ambiance | bass, aecho, highpass |
| `whisper` | Realistic whisper | highpass, treble, bass cut, reverb |
| `breathy` | Breathed voice with intimate presence | highpass, bass, treble, aecho, compressor |
| `emphatic` | Emphasis and clarity | compressor, bass, treble, volume boost |
| `radio` | Intercom/radio effect | bandpass, heavy compression, volume |
| `processed` | Lab/radio processing effect | bass, overdrive, reverb |

## How Effects Are Applied

### Per-Segment Effects

When processing annotated text like `Hello <whisper>secret</whisper>`:

1. Text is parsed into segments: `[("Hello ", "normal"), ("secret", "whisper")]`
2. Each segment is synthesized by Piper
3. The voice config's mode is looked up (e.g., `whisper` → `["whisper"]`)
4. The effect chain is applied via ffmpeg
5. The segment is dynamically normalized (LUFS-based)

### Effect Chains

A mode can reference multiple effects, applied in sequence:

```json
"modes": {
  "robotic": { "effects": ["processed", "radio"] }
}
```

```
Raw audio → processed effect → radio effect → Normalized output
```

### Global Effects

After all segments are concatenated, the voice's `global_effects` are applied once to the complete audio, followed by the master bus.

## Master Bus

The `master_bus.json` file defines effects applied to **all** generated audio, regardless of voice or mode:

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

The `normalization` section configures the per-segment dynamic normalization parameters.

## Adding a New Effect

1. **Create the JSON file** in `effects/my_effect.json`:
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

2. **Reference it in a voice config** mode:
   ```json
   "modes": {
     "custom": { "effects": ["my_effect"] }
   }
   ```

3. **Restart the server**. The effect loads automatically.

## Common FFmpeg Filters

| Filter | Purpose | Example |
|--------|---------|---------|
| `bass=g=X:f=Y` | Boost/cut bass | `bass=g=3:f=200` |
| `treble=g=X:f=Y` | Boost/cut treble | `treble=g=6:f=2500` |
| `highpass=f=X` | Remove low frequencies | `highpass=f=600` |
| `lowpass=f=X` | Remove high frequencies | `lowpass=f=3500` |
| `aecho=in_gain:vol:delay:decay` | Reverb/echo | `aecho=0.8:0.9:40:0.3` |
| `acompressor=...` | Dynamic compression | `acompressor=threshold=-30dB:ratio=4:attack=10:release=50` |
| `alimiter=...` | Peak limiting | `alimiter=limit=-0.5dB:attack=3:release=20` |
| `volume=X` | Volume adjustment | `volume=+6dB` |
| `loudnorm=...` | EBU R128 loudness normalization | `loudnorm=I=-16:TP=-1.5:LRA=11` |

## Custom Effect Processors

To implement a non-ffmpeg processor (e.g., Python/numpy-based):

1. **Create the processor** in `src/effects/my_processor.py`:
   ```python
   from .base import EffectBase

   class MyProcessor(EffectBase):
       name = "my_type"
       effect_type = "python"

       def apply(self, audio_bytes: bytes, config: dict) -> bytes:
           # Your processing logic here
           return audio_bytes
   ```

2. **Register it** in `src/effects/registry.py`:
   ```python
   from .my_processor import MyProcessor

   self._processors: Dict[str, EffectBase] = {
       "ffmpeg": FFmpegEffect(ffmpeg_path=ffmpeg_path),
       "python": MyProcessor(),
   }
   ```

3. **Use it** in an effect definition:
   ```json
   {
     "name": "my_effect",
     "type": "python",
     "filters": []
   }
   ```

## Sample Rate Handling

All effects automatically detect and preserve the input audio's sample rate and channel count. No resampling occurs during effect processing.

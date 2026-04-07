# OpenClaw Plugin for LAPIS-TTS

OpenClaw speech provider plugin for LAPIS-TTS - Local text-to-speech with advanced voice effects invisible to the user.

## Features

- **Invisible Voice Effects**: Tags like `[[tts:text]]<whisper>secret</whisper>[[/tts:text]]` are heard but not shown in chat
- **Cue Transformation**: Automatic conversion of model cues to LAPIS tags:
  - `(whisper)` → `<whisper>`
  - `(robotic)` → `<robotic>`
  - `(emphatic)` → `<emphatic>`
  - And 8+ more effects
- **Professional Logging**: Debug, info, and error levels with configurable output
- **Emoji Sanitization**: Automatic cleanup of problematic Unicode characters for TTS

## Installation

### Method 1: Local Installation (Development)

```bash
# Clone the LAPIS-TTS repository
git clone https://github.com/fr4j4/lapis-tts.git
cd lapis-tts

# Install the plugin in OpenClaw
openclaw plugins install ./plugin-lapis-tts
```

### Method 2: Install from Git (Production)

```bash
openclaw plugins install https://github.com/fr4j4/lapis-tts/tree/master/plugin-lapis-tts
```

## Quick Configuration

Add to your `openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "lapis-tts": {
        "enabled": true,
        "config": {
          "baseUrl": "http://localhost:3000",
          "voice": "davefx-es",
          "timeoutMs": 30000
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
          "voice": "davefx-es",
          "timeoutMs": 30000
        }
      }
    }
  }
}
```

Then restart the Gateway:

```bash
openclaw gateway restart
```

## Usage

### Invisible Voice Effects

When `auto` is set to `"tagged"`, the model can emit text with effects that are only heard:

**Model response:**
```
Welcome to the enrichment center.
[[tts:text]](whisper)The cake was a lie(/whisper)[[/tts:text]]
Let's continue with the tests.
```

**The user sees:**
> Welcome to the enrichment center. Let's continue with the tests.

**The user hears:**
1. "Welcome to the enrichment center" (normal voice)
2. *whisper* "The cake was a lie"
3. "Let's continue with the tests" (normal voice)

### TTS Modes

| Mode | Description |
|------|-------------|
| `"off"` | TTS disabled |
| `"always"` | Always generates audio for all responses |
| `"inbound"` | Only generates audio if the inbound message was voice |
| `"tagged"` | Only generates audio if `[[tts:text]]` tags are present in the response |

### Supported Cues

| Cue | Effect |
|-----|--------|
| `(whisper)` / `(/whisper)` | Whisper |
| `(robotic)` / `(/robotic)` | Robotic voice |
| `(emphatic)` / `(/emphatic)` | Emphasis |
| `(dramatic)` / `(/dramatic)` | Dramatic |
| `(radio)` / `(/radio)` | Radio effect |
| `(phone)` / `(/phone)` | Phone effect |
| `(breathy)` / `(/breathy)` | Intimate voice |
| `(intimate)` / `(/intimate)` | Intimate |
| `(menacing)` / `(/menacing)` | Menacing tone |
| `(threatening)` / `(/threatening)` | Threatening tone |

### Model Configuration

To let the model use these effects, add to your system prompt:

```
You can use voice effects with this format:
[[tts:text]](effect)text(/effect)[[/tts:text]]

Available effects:
- (whisper)text(/whisper) - Whisper
- (robotic)text(/robotic) - Robotic voice
- (emphatic)text(/emphatic) - Emphasis
- (menacing)text(/menacing) - Menacing tone
- (dramatic)text(/dramatic) - Dramatic
- (radio)text(/radio) - Radio effect
- (breathy)text(/breathy) - Intimate voice

Text inside [[tts:text]] will be heard but not shown to the user.
```

### Model Directives

OpenClaw allows the model to override settings for a single response:

```
Here is your response.

[[tts:voiceId=robot-es model=eleven_v3 speed=1.1]]
[[tts:text]](robotic)Processing data...(/robotic)[[/tts:text]]
```

## Available Voices

Voices depend on the ONNX models in `~/lapis-tts/voices/`:

| Voice ID | Description |
|----------|-------------|
| `davefx-es` | Spanish narrator (Spain) |
| `robot-es` | GLaDOS Spanish (Spain) |
| `ald-mx` | Mexican voice |
| `mls-es` | MLS Spanish (light) |
| `lessac-en` | English US male |
| `amy-en` | English US female |
| `ryan-en` | English US male |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  OpenClaw   │────▶│ LAPIS-TTS    │────▶│ Piper TTS   │
│  (Gateway)  │◄────│ Plugin       │◄────│ (ONNX)      │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                               
       │ Extracts [[tts:text]]                           
       │ Transforms cues → tags                       
       │ POST /v1/text-to-speech/{voice}              
```

## Troubleshooting

### Plugin does not appear in `openclaw plugins list`

```bash
openclaw plugins remove lapis-tts
openclaw plugins install ./plugin-lapis-tts
openclaw gateway restart
```

### "LAPIS-TTS request failed"

Verify LAPIS is running:
```bash
curl http://localhost:3000/health
# Should return: {"status":"ok"}
```

### Audio not generated with tags

1. Verify `messages.tts.auto` is set to `"tagged"`
2. Verify `messages.tts.modelOverrides.enabled` is `true`
3. Verify the model includes `[[tts:text]]` in its response

### Tags visible in chat

If `[[tts:text]]` tags appear in the chat:
- Verify the plugin is installed and active
- Verify plugin version is 1.1.0 or higher
- Verify correct configuration in `openclaw.json`

## Installation Verification

```bash
# Verify plugin loaded
openclaw plugins list

# Verify LAPIS responds
curl http://localhost:3000/health

# Test TTS
openclaw tts "Hello world" --provider lapis
```

## Requirements

- LAPIS-TTS server running at the configured `baseUrl`
- OpenClaw 2026.4+ with speech provider support

## Resources

- [LAPIS-TTS Repository](https://github.com/fr4j4/lapis-tts)
- [OpenClaw TTS Documentation](https://docs.openclaw.ai/tools/tts)
- [OpenClaw Plugins](https://docs.openclaw.ai/plugins)

## Support

- GitHub Issues: https://github.com/fr4j4/lapis-tts/issues
- Discussions: https://github.com/fr4j4/lapis-tts/discussions

## License

MIT - See LICENSE in the main repository

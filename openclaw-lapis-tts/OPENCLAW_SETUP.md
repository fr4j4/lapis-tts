# LAPIS-TTS + OpenClaw Setup

## 1. Install plugin
```bash
openclaw plugins install ./openclaw-lapis-tts
```

## 2. Enable TTS in openclaw.json

Add to `plugins.entries`:
```json
"lapis-tts": { "enabled": true, "config": { "voice": "davefx-es" } }
```

Set TTS mode:
```json
"messages.tts": { "auto": "always", "provider": "lapis" }
```

## 3. Enable Discord voice
```json
"channels.discord.voice.enabled": true
```

## 4. Add voice instructions to SOUL.md

Append this to `~/.openclaw/workspace/SOUL.md`:

```markdown
## Voice Effects (LAPIS-TTS)

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

## Voice Modes Reference

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

## Example Response with Effects

```
Welcome to the enrichment center.
[[tts:text]](whisper)The cake was a lie(/whisper)[[/tts:text]]
Let's continue with the tests.
```

User sees: "Welcome to the enrichment center. Let's continue with the tests."
User hears: Normal voice → whisper effect → normal voice
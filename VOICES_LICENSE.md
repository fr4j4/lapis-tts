# Voice Licenses

This project includes open-source TTS voices. Below is the documentation of included voices and their original licenses.

## Project License

MIT License - See LICENSE file in the project root.

## Included Voices

### English (US)

| Voice ID | Model | Quality | Original License | Dataset |
|----------|-------|---------|-----------------|---------|
| `lessac-en` | `en_US-lessac-high` | High | MIT | LJ Speech |
| `amy-en` | `en_US-amy-medium` | Medium | MIT | LJ Speech |
| `ryan-en` | `en_US-ryan-medium` | Medium | MIT | Personal |

### Spanish (Mexico)

| Voice ID | Model | Quality | Original License | Dataset |
|----------|-------|---------|-----------------|---------|
| `claude-es` | `es_MX-claude-high` | High | MIT | Personal |
| `ald-mx` | `es_MX-ald-medium` | Medium | MIT | Personal |

### Spanish (Spain)

| Voice ID | Model | Quality | Original License | Dataset |
|----------|-------|---------|-----------------|---------|
| `davefx-es` | `es_ES-davefx-medium` | Medium | MIT | MLS |
| `mls-es` | `es_ES-mls_9972-low` | Low | MIT | MLS |

## Original Datasets

### LJ Speech Dataset
- **License:** Public Domain
- **Source:** https://keithito.com/LJ-Speech-Dataset/
- **Content:** 13,100 short audio clips of a single speaker reading passages from 7 non-fiction books

### MLS (Multilingual LibriSpeech)
- **License:** CC BY 4.0
- **Source:** https://github.com/facebookresearch/mls
- **Content:** Speech data in multiple languages

### VCTK (Voice Cloning Toolkit)
- **License:** CC BY-NC-SA 4.0 (NON-COMMERCIAL)
- **Source:** https://datashare.ed.ac.uk/handle/10283/2950
- **Note:** Voices trained with VCTK are NOT included in this project

## Inactive Voices

The voices `robot-en` and `robot-es` are configured but disabled (`active: false`) for testing purposes.

## Notes

1. **Commercial Use:** All active voices in this project have licenses that allow commercial use (MIT or Public Domain).

2. **Attribution:** When using this project, attribution to the original voice and dataset creators is recommended.

## Sources

- Piper Voices: https://huggingface.co/rhasspy/piper-voices
- Piper Documentation: https://github.com/rhasspy/piper

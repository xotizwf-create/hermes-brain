---
name: generative-media-production
description: "Use when generating or transforming media assets: ASCII art/video, pixel art, Manim animations, ComfyUI images/video/audio, TouchDesigner visuals, GIFs, music prompts, audio features, and YouTube-derived content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [media, image-generation, video, audio, ascii, pixel-art, animation]
    related_skills: []
---

# Generative Media Production

## Overview

Umbrella for media-generation and media-transformation workflows. Choose the medium and delivery format first, then use the specialized toolchain while verifying real files/URLs before reporting success.

## When to Use

- ASCII art or ASCII video/GIF conversion.
- Pixel art stills or pixel-art video.
- Manim/3Blue1Brown-style explanatory animations.
- ComfyUI image/video/audio workflows.
- TouchDesigner real-time visuals via MCP.
- Text-to-speech / voice-message generation, including comparing voice personas and delivering Telegram voice notes.
- GIF search/download, audio feature/spectrogram analysis, HeartMuLa/Suno-style music prompts, Spotify/media operations, YouTube transcript-derived outputs.

## Router

| Need | Route |
|---|---|
| Text/terminal visual gag | ASCII art |
| Video/audio to colored ASCII | ASCII video |
| Retro sprites/palettes | Pixel art |
| Mathematical/explainer animation | Manim |
| Node-based image/video/audio generation | ComfyUI |
| Real-time interactive visuals | TouchDesigner |
| Text → Telegram voice note | TTS voice workflow |
| Existing GIF reaction | GIF search |
| Song generation prompt/lyrics | Songwriting/HeartMuLa |
| Audio analysis | Songsee-style feature extraction |
| YouTube transcript to content | YouTube content workflow |

## Common Workflow

1. Identify input assets, output format, dimensions/duration, and style constraints.
2. Check required commands/models/nodes before starting long renders.
3. Generate into a clear output directory.
4. Validate the artifact exists and is viewable/playable/analyzable.
5. Deliver `MEDIA:<path>` or URL where supported.

## TTS Voice Workflow

Use this when the user asks for a spoken answer, voice samples, or switching between voice personas.

1. Prefer the built-in `text_to_speech` tool for the currently configured default voice when no custom voice parameters are needed.
2. For explicit voice comparisons or style variants, use the configured TTS CLI directly when available (e.g. `edge-tts`) so you can set voice, pitch, and rate, then deliver the generated file as `MEDIA:<absolute_path>`.
3. Verify the command succeeded and the file path is absolute before replying; Telegram should receive a real media attachment, not just a path string.
4. For Александр's baseline Russian voices, use:
   - masculine / rougher: `ru-RU-DmitryNeural`, lower pitch (about `--pitch=-12Hz`) and slightly slower (`--rate=-5%`)
   - feminine / softer: `ru-RU-SvetlanaNeural`, slightly higher pitch (about `--pitch=+8Hz`) and slightly slower (`--rate=-3%`)
5. When the user asks for profanity or edgy voice demos, keep it playful and non-targeted; avoid slurs, threats, or abuse directed at a real person/group.

Example:

```bash
mkdir -p /root/.hermes/audio_cache
edge-tts --voice ru-RU-SvetlanaNeural --pitch=+8Hz --rate=-3% \
  --text 'Короткий пример мягкого женского голоса.' \
  --write-media /root/.hermes/audio_cache/tts_demo.ogg
```

## Pitfalls

- Claiming render success without checking the output file.
- Starting long GPU/model workflows without dependency and disk checks.
- Losing palette/style consistency across frames.
- Confusing prompt-only music generation with actual audio rendering.

## Verification Checklist

- [ ] Medium/toolchain selected.
- [ ] Dependencies/assets checked.
- [ ] Artifact generated or fetched.
- [ ] Output file/URL verified.

---
name: baoyu-visual-content
description: "Use when producing Baoyu-style visual content: article illustrations, educational comics, and structured infographics with consistent prompts, palettes, layouts, and workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [baoyu, image-generation, infographic, comic, illustration, visual-summary]
    related_skills: []
---

# Baoyu Visual Content

## Overview

Umbrella for the Baoyu/JimLiu visual-generation family. Choose the output form first, preserve source facts, then assemble a high-quality prompt from structure + style + palette/layout references.

## When to Use

- Article/header/support illustrations with style and palette consistency.
- Knowledge comics (知识漫画), biographies, educational/tutorial panels.
- Infographics, visual summaries, information graphics, 高密度信息大图, 可视化.

## Output-Form Router

| User asks for | Choose | Core decision |
|---|---|---|
| Article illustration, cover, visual metaphor | Article illustration | illustration type × style × palette |
| Comic, manga-like explainer, panels | Comic | story arc × panel count × character/setting continuity |
| Infographic, visual summary, structured poster | Infographic | layout × visual style × aspect ratio |

## Shared Workflow

1. Analyze source content and audience; detect language.
2. Extract user design constraints (style, palette, aspect, text language).
3. Preserve facts exactly; strip secrets before prompt generation.
4. Choose visual structure: illustration type, comic storyboard, or infographic layout.
5. Confirm key options when they materially change the output.
6. Generate prompt and image; retry once on generation failure.
7. Report selected structure/style, aspect, language, and output path/URL.

## Subsections

### Article Illustrations

Prioritize one strong visual metaphor and consistent palette. Keep text minimal unless the user explicitly wants captions or labels.

### Comics

Break knowledge into scenes/panels. Maintain character identity and visual continuity across panels. Use storyboard templates for educational sequence or biography arc.

### Infographics

Map information structure to layout (timeline, comparison, hierarchy, dashboard, dense modules, etc.) and style (craft, schematic, cyberpunk, corporate, hand-drawn education, etc.). Preserve all statistics/quotes verbatim.

## Pitfalls

- Mixing multiple styles in one asset.
- Paraphrasing source statistics in an infographic.
- Overloading a panel/section with too many concepts.
- Forgetting that image tools usually expose only landscape/portrait/square, so custom ratios need nearest mapping.

## Verification Checklist

- [ ] Output form selected deliberately.
- [ ] Facts preserved and secrets stripped.
- [ ] Style/palette/layout choices recorded.
- [ ] Generated artifact URL/path delivered.

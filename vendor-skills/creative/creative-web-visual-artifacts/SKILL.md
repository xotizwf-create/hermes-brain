---
name: creative-web-visual-artifacts
description: "Use when creating visual artifacts as HTML/SVG/JSON/browser demos: architecture diagrams, Excalidraw sketches, landing/mockup designs, p5.js/pretext demos, design tokens, and visual style references."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, html, svg, diagrams, mockups, p5js, excalidraw, design]
    related_skills: []
---

# Creative Web & Visual Artifacts

## Overview

Class-level workflow for visual deliverables that are code or structured files rather than only prose: HTML mockups, SVG architecture diagrams, Excalidraw scenes, p5.js sketches, Pretext text-layout demos, design token specs, and style-system references.

## When to Use

- Dark SVG/cloud/infra architecture diagrams.
- Hand-drawn Excalidraw JSON diagrams.
- One-off landing pages, decks, prototypes, or 2–3 design variants.
- p5.js generative art, shaders, interactions, 3D, frame export.
- Pretext text-as-geometry browser demos.
- DESIGN.md token specs or popular-web-design-inspired visual systems.

## Standard Workflow

1. Clarify artifact type, audience, dimensions/aspect, and required interactivity.
2. Create a self-contained file when possible (HTML/CSS/JS or JSON).
3. Use project-specific templates/reference systems only when they improve fidelity.
4. Render or open in browser when feasible; fix visible/layout errors.
5. Deliver the file path and summarize how to view/edit it.

## Artifact Subtypes

### Architecture/SVG Diagrams

Use clear grouping, labels, arrows, and dark-theme contrast. Prefer semantic layout over decorative complexity.

### Excalidraw

Generate valid Excalidraw JSON with consistent rough style, colors, and connectors. Use upload helpers only after file validation.

### HTML Mockups and Design Systems

For exploratory design, produce multiple variants quickly. For polished output, borrow spacing/type/color patterns from real systems and keep responsive behavior sane.

### p5.js / Pretext Demos

Keep demos single-file unless the user requests a project. Include setup/render/export instructions and verify in a browser or headless render when possible.

### DESIGN.md

Validate frontmatter/token syntax and provide export/use notes.

## Pitfalls

- Delivering static prose instead of the requested artifact file.
- Not rendering a visual artifact before claiming it works.
- Mixing incompatible style systems in one mockup.
- Forgetting that Excalidraw and p5.js have strict schema/runtime expectations.

## Verification Checklist

- [ ] Artifact file written.
- [ ] Syntax/schema/runtime checked.
- [ ] Visual rendering inspected when possible.
- [ ] User received path and viewing instructions.

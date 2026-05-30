---
name: markitdown-docs
description: "Use when the owner sends or references local document files that should be read before answering: PDF, Word (.docx), Excel (.xlsx/.xls), PowerPoint (.pptx), CSV/HTML/text-like exports, or ZIPs containing documents. Convert files with Microsoft MarkItDown to compact Markdown first, then inspect the Markdown instead of sending binary Office/PDF content into the model context."
---

# Skill: markitdown-docs

## Overview

Convert document files into Markdown before analysis. This keeps context smaller, preserves useful
structure such as headings, lists, links and tables, and avoids wasting model tokens on raw binary or
layout-heavy Office/PDF content.

Source tool: Microsoft MarkItDown (`microsoft/markitdown`). It supports PDF, PowerPoint, Word,
Excel, images/OCR metadata, audio metadata/transcription, HTML, CSV/JSON/XML, ZIP contents, YouTube
URLs, EPUBs, and more. For this agent, use it primarily for local PDF/Office files.

Manager: `skills/markitdown-docs/scripts/convert_document.py` -> prod
`/root/.hermes/agent-knowledge/skills/markitdown-docs/scripts/convert_document.py`.

## Default workflow

1. If the user provides a local document file, run the converter before reasoning over the content:

```bash
python3 /root/.hermes/agent-knowledge/skills/markitdown-docs/scripts/convert_document.py "/path/to/file.pdf"
```

2. Use the generated Markdown file printed by the script. Search or read only the relevant parts:

```bash
rg -n "contract|price|deadline|action item" "/path/to/file.markitdown.md"
sed -n '1,160p' "/path/to/file.markitdown.md"
```

3. Answer from the Markdown. Do not paste full long conversions into chat unless the owner explicitly
asks for the raw extracted text.

## Install prerequisite

MarkItDown requires Python 3.10+. Install it in the same Python environment used by Hermes terminal
tools:

```bash
python3 -m pip install "markitdown[pdf,docx,pptx,xlsx,xls]"
```

If that fails inside the Hermes venv, run the venv Python explicitly:

```bash
/usr/local/lib/hermes-agent/venv/bin/python -m pip install "markitdown[pdf,docx,pptx,xlsx,xls]"
```

## Usage

Write Markdown next to the source file and print a short preview:

```bash
python3 skills/markitdown-docs/scripts/convert_document.py ./report.xlsx
```

Choose an output path:

```bash
python3 skills/markitdown-docs/scripts/convert_document.py ./slides.pptx -o /tmp/slides.md
```

Print a larger preview only when the document is small or the owner asks for extracted text:

```bash
python3 skills/markitdown-docs/scripts/convert_document.py ./contract.docx --stdout --preview-chars 50000
```

## Rules

- Prefer local file conversion. Do not pass arbitrary URLs to MarkItDown; use `read-links` for URLs.
- Do not enable plugins or LLM image descriptions by default. They can add cost and make behavior less
  predictable.
- For scanned PDFs or image-heavy slides where normal extraction returns little text, say that OCR is
  needed before making strong claims.
- Keep the generated `.markitdown.md` as a working artifact only. Commit it only if the user asks or it
  is intentionally becoming knowledge.
- If the converter fails because the package is missing, install MarkItDown in the active Hermes
  Python environment, then rerun the same command.

---
name: document-production-workflows
description: "Use when creating, converting, extracting, or editing documents and office artifacts: Word academic papers, PowerPoint decks, PDFs, OCR/scans, meeting summaries, and contract/document pipelines."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documents, word, powerpoint, pdf, ocr, contracts, meetings]
    related_skills: []
---

# Document Production Workflows

## Overview

Umbrella for document-heavy work: produce editable artifacts, preserve formatting/data, verify generated files, and use OCR/conversion only as a means to the requested document result.

## When to Use

- Russian academic Word documents/coursework-style assignments.
- PowerPoint creation, reading, editing, notes, templates.
- PDF typo/title/text edits.
- OCR or Markdown extraction from PDFs/scans.
- Teams/meeting summary pipelines.
- Contract processing in domain-specific systems.
- Excel/CSV deliverables built from researched or computed data, especially when the user requests “в виде таблицы / формат Excel”.

## Common Workflow

1. Identify source files, target format, language/style, and required template/standard.
2. Extract/read source text with the least lossy method.
3. Create or edit the artifact using a format-aware library/tool.
4. Validate the resulting file opens/parses and contains the expected content.
5. Provide the file path/attachment and concise change summary.

## Subdomains

### Word / Academic Documents

Follow requested academic structure, tables/figures/captions, and ГОСТ-like formatting when relevant. Avoid obviously AI-sounding filler.

### PowerPoint

Keep slide structure, notes, and media paths consistent. Validate the `.pptx` package after edits.

### Excel / Spreadsheet Reports

When the user asks for Excel, deliver a real `.xlsx`, not just a Markdown table. Use `pandas`/`openpyxl` or another format-aware writer, add readable headers/widths/wrapping when helpful, and save owner-facing files under `/root/.hermes/outbox/` for Telegram delivery. Before replying, reopen the workbook and verify sheet names, row/column counts, and at least one expected row/value. If the data came from public research or computations, include a source/notes column or separate notes sheet so the artifact is self-explanatory.

### PDF and OCR

Use OCR/extraction to obtain text, but verify coordinates/pages before editing PDFs. Report OCR uncertainty when scans are poor.

When the user asks for a report/document “from the database” as PDF, treat the saved database text as the source of truth, then build and deliver a real PDF attachment. For Russian reports, use an embedded Unicode font (for example DejaVu via ReportLab) to avoid mojibake on phones. Preserve Markdown headings, bullets, and tables where practical; use landscape pages for wide management tables. Verify the artifact before replying: file exists, starts with `%PDF-`, has non-trivial size, and text extraction via `pdfminer`/similar contains the expected title/period. If a CLI extractor is missing or returns empty due to fonts, use a Python PDF library fallback rather than assuming failure.

### Meeting and Contract Pipelines

Respect domain-specific MCP/tool prompts and confirmation rules before saving or dispatching tasks.

## Pitfalls

- Returning prose instead of the requested editable file.
- Trusting OCR blindly for legal/financial fields.
- Editing a PDF without verifying the changed page visually or structurally.
- Creating downstream tasks/contracts before required confirmations.

## Verification Checklist

- [ ] Source read/extracted.
- [ ] Artifact written.
- [ ] File validated/opened or parsed.
- [ ] User got path or media attachment.

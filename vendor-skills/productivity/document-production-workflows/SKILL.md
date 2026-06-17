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
- ГОСТ-style research reports and PDF deliverables that combine source-backed analysis with formal Russian document formatting.

## Common Workflow

1. Identify source files, target format, language/style, and required template/standard.
2. Extract/read source text with the least lossy method.
3. Create or edit the artifact using a format-aware library/tool.
4. Validate the resulting file opens/parses and contains the expected content.
5. Provide the file path/attachment and concise change summary.
6. For owner-facing deliverables, route delivery from the user's wording: “пришли/прислать мне” means deliver back to the current Telegram/user chat (usually as a real attachment from `/root/.hermes/outbox/`), not to a third party mentioned in the source material. Only email an external person when the user explicitly says to send/email/forward to that person and the recipient is confirmed.

## Subdomains

### Word / Academic Documents

Follow requested academic structure, tables/figures/captions, and ГОСТ-like formatting when relevant. Avoid obviously AI-sounding filler.

### PowerPoint

Keep slide structure, notes, and media paths consistent. Validate the `.pptx` package after edits.

### Excel / Spreadsheet Reports

When the user asks for Excel, deliver a real `.xlsx`, not just a Markdown table. Use `pandas`/`openpyxl` or another format-aware writer, add readable headers/widths/wrapping when helpful, and save owner-facing files under `/root/.hermes/outbox/` for Telegram delivery. Before replying, reopen the workbook and verify sheet names, row/column counts, and at least one expected row/value. If the data came from public research or computations, include a source/notes column or separate notes sheet so the artifact is self-explanatory.

### ГОСТ-style Reports and Source-Backed PDFs

When the user requests a formal PDF report “по ГОСТ” from research findings, create an editable source document first (`.docx` when practical), then convert to PDF with LibreOffice/headless tooling. Use a formal Russian structure: title page, contents/sections, source methodology, main tables/schemes, limitations, and source list/appendix. Keep evidentiary caveats inside the report rather than only in the chat reply (for example, unresolved AO shareholder layers that require register extracts). Save owner-facing files under `/root/.hermes/outbox/`, verify the PDF exists, has non-trivial size, opens/parses, and contains expected title/key sections before sending via `MEDIA:`.

### PDF and OCR

Use OCR/extraction to obtain text, but verify coordinates/pages before editing PDFs. Report OCR uncertainty when scans are poor.

When the user asks for a report/document “from the database” as PDF, treat the saved database text as the source of truth, then build and deliver a real PDF attachment. For Russian reports, use an embedded Unicode font (for example DejaVu via ReportLab) to avoid mojibake on phones. Preserve Markdown headings, bullets, and tables where practical; use landscape pages for wide management tables. Verify the artifact before replying: file exists, starts with `%PDF-`, has non-trivial size, and text extraction via `pdfminer`/similar contains the expected title/period. If a CLI extractor is missing or returns empty due to fonts, use a Python PDF library fallback rather than assuming failure.

### Meeting and Contract Pipelines

Respect domain-specific MCP/tool prompts and confirmation rules before saving or dispatching tasks.

For «Простые поставки» incoming contract documents, use `references/prostye-postavki-incoming-contracts.md`: read the MCP prompt first, save parsed fields, search duplicates before creating/updating, then read back the visible contract card and verify line-item quantity/price/sum/total. Do not report completion if the connector saved extracted data but the created card shows mis-mapped prices or totals.

For legacy Word `.doc` contracts that need a few field/specification edits, use the workflow in `references/legacy-doc-contract-editing.md`: convert a copy to `.docx` with LibreOffice headless, edit targeted paragraphs/table cells with `python-docx`, verify required values and absence of stale values, confirm the file opens by converting to PDF, then render/inspect changed PDF pages so tables/prices did not shift before sending Word+PDF.

## Pitfalls

- Returning prose instead of the requested editable file.
- Trusting OCR blindly for legal/financial fields.
- Editing a PDF without verifying the changed page visually or structurally.
- Creating downstream tasks/contracts before required confirmations.
- Inferring an external recipient from the document/email context and sending there when the owner asked to “send me” the finished document.

## Verification Checklist

- [ ] Source read/extracted.
- [ ] Artifact written.
- [ ] File validated/opened or parsed.
- [ ] User got path or media attachment.

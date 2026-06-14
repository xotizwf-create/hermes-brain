---
name: markitdown-docs
description: "Use when converting documents and rich files to Markdown with Microsoft MarkItDown, especially PDFs, Office files, HTML, images, audio, archives, or URLs. Install or verify markitdown, run conversions safely, preserve useful structure, and choose OCR/fallback tools when MarkItDown is not enough."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [markitdown, markdown, documents, pdf, office, conversion, extraction]
    related_skills: [ocr-and-documents, nano-pdf, notion, llm-wiki]
---

# MarkItDown Documents

## Overview

Use this skill to convert documents and rich files into Markdown using Microsoft MarkItDown. MarkItDown is best for agent-friendly extraction: it turns files into readable Markdown that can be summarized, searched, chunked, indexed, or copied into notes and knowledge bases.

MarkItDown is usually the first choice when the user wants a Markdown representation of a document rather than a visual edit of the original file. For scanned documents or image-heavy PDFs, pair it with OCR tools from `ocr-and-documents`.

## When to Use

Use this skill when the user asks to:

- convert a PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, image, audio, ZIP, or URL to Markdown
- extract readable text from a document while preserving headings, lists, tables, links, and metadata where possible
- prepare documents for RAG, search indexes, summaries, Obsidian/Notion notes, or LLM context
- batch-convert a folder of documents into `.md` files
- compare MarkItDown output with OCR output and choose the cleaner result

Do not use this skill when:

- the user wants to edit text inside an existing PDF — use `nano-pdf`
- the document is a scan with no embedded text and MarkItDown returns little content — use `ocr-and-documents`
- the task is about designing or validating `DESIGN.md` files — use `design-md`

## Quick Checks

Before converting, check whether MarkItDown is available:

```bash
python - <<'PY'
import importlib.util
print('markitdown', 'available' if importlib.util.find_spec('markitdown') else 'missing')
PY
```

If the command-line entry point exists, this may also work:

```bash
markitdown --help
```

If it is missing and installing packages is acceptable for the task, install it:

```bash
python -m pip install -U markitdown
```

For optional file types, MarkItDown may require extras depending on the environment. If conversion fails because a parser dependency is missing, install the relevant extra or fallback to `ocr-and-documents`.

## Basic Conversion

Preferred Python API:

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert('/path/to/input.pdf')
text = result.text_content

with open('/path/to/output.md', 'w', encoding='utf-8') as f:
    f.write(text)
```

Command-line form when available:

```bash
markitdown /path/to/input.pdf > /path/to/output.md
```

For URLs:

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert('https://example.com/page')
print(result.text_content)
```

## Recommended Workflow

1. Identify the input type and the user's desired output: one Markdown file, a folder of Markdown files, summary, structured fields, or RAG-ready chunks.
2. If the user refers to uploaded/attached documents but paths are not explicit, search likely attachment caches before asking them to re-upload. In Hermes/Telegram sessions, check the current working directory, `/tmp`, and `~/.hermes/cache/documents/`, filtering by relevant extensions and recent modification time.
3. Check MarkItDown availability.
4. Convert with MarkItDown and save output as UTF-8 `.md`.
5. Inspect the output size and first/last sections to catch empty or garbled conversions.
5. If output is poor:
   - for scanned PDFs/images: use OCR from `ocr-and-documents`
   - for PDF visual text extraction issues: try PyMuPDF or marker-pdf from `ocr-and-documents`
   - for tables/spreadsheets: consider preserving the original CSV/XLSX structure separately
6. Deliver the Markdown file or use it for the requested downstream task.

## Output Quality Checks

After conversion, verify:

- output is not empty or only metadata
- headings and list structure are reasonably preserved
- tables are readable enough for the user's task
- no obvious binary garbage or repeated page headers dominate the result
- secrets, tokens, passwords, and private keys are not exposed in chat; redact as `[REDACTED]` if encountered

Useful quick inspection:

```bash
wc -c /path/to/output.md
python - <<'PY'
from pathlib import Path
p = Path('/path/to/output.md')
text = p.read_text(encoding='utf-8', errors='replace')
print(text[:2000])
print('\n--- END PREVIEW ---\n')
print(text[-1000:])
PY
```

## Batch Conversion Recipe

Use this pattern for a folder of mixed documents:

```python
from pathlib import Path
from markitdown import MarkItDown

src = Path('/path/to/input-folder')
out = Path('/path/to/output-markdown')
out.mkdir(parents=True, exist_ok=True)

md = MarkItDown()
for path in src.rglob('*'):
    if not path.is_file():
        continue
    if path.suffix.lower() in {'.md', '.txt'}:
        continue
    try:
        result = md.convert(str(path))
        text = result.text_content or ''
    except Exception as exc:
        print(f'SKIP {path}: {exc}')
        continue
    if not text.strip():
        print(f'EMPTY {path}')
        continue
    target = out / path.relative_to(src).with_suffix('.md')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    print(f'OK {path} -> {target}')
```

## Pairing With Other Skills

- `ocr-and-documents`: use when MarkItDown cannot read scanned PDFs/images or when layout-aware extraction is required
- `nano-pdf`: use when the user wants to edit the original PDF rather than convert it
- `notion`: use after conversion when the Markdown should become a Notion page
- `llm-wiki`: use after conversion when the Markdown should become a linked knowledge base

## Common Pitfalls

1. **Assuming a PDF has selectable text.** If MarkItDown returns little or nothing, the PDF may be scanned. Switch to OCR.
2. **Treating Markdown as a faithful visual copy.** Markdown is semantic text, not a layout-preserving PDF replacement.
3. **Dumping sensitive document contents into chat.** Preview only what is necessary and redact secrets as `[REDACTED]`.
4. **Overwriting outputs in batch jobs.** Preserve relative paths and use unique output directories.
5. **Ignoring tables.** Markdown tables from complex PDFs or spreadsheets may need manual cleanup or a spreadsheet-specific extraction pass.
6. **Installing packages without need.** Check first; if MarkItDown is already installed, use the existing environment.
7. **Assuming attachments are in the working directory.** Messaging-platform uploads may be staged in profile caches such as `~/.hermes/cache/documents/`; search recent files by extension and mtime before asking the user to resend.

## Verification Checklist

- [ ] MarkItDown availability checked or installed intentionally
- [ ] Input file/path/URL confirmed
- [ ] Markdown output saved as UTF-8
- [ ] Output inspected for emptiness, garbage, and obvious structure problems
- [ ] OCR fallback used when the source is scanned or image-only
- [ ] Sensitive values redacted from user-facing previews
- [ ] Final response includes where the Markdown file was saved or a concise summary of the conversion result

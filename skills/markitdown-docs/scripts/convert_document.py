#!/usr/bin/env python3
"""Convert a local document to Markdown with Microsoft MarkItDown."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SUPPORTED_HINT = ".pdf, .docx, .xlsx, .xls, .pptx, .csv, .html, .htm, .json, .xml, .txt, .zip, .epub"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a local document to Markdown with Microsoft MarkItDown."
    )
    p.add_argument("file", help="local file to convert")
    p.add_argument(
        "-o",
        "--out",
        help="output Markdown path; default is <source>.markitdown.md next to the source",
    )
    p.add_argument(
        "--preview-chars",
        type=int,
        default=12000,
        help="characters to print as preview after writing the full Markdown (default: 12000)",
    )
    p.add_argument(
        "--stdout",
        action="store_true",
        help="print Markdown preview to stdout without writing an output file",
    )
    return p.parse_args()


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def convert_with_markitdown(source: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError:
        die(
            "MarkItDown is not installed. Install it with:\n"
            '  python3 -m pip install "markitdown[pdf,docx,pptx,xlsx,xls]"'
        )

    md = MarkItDown(enable_plugins=False)
    if hasattr(md, "convert_local"):
        result = md.convert_local(str(source))
    else:
        result = md.convert(str(source))

    text = getattr(result, "markdown", None) or getattr(result, "text_content", None)
    if text is None:
        die("MarkItDown returned no Markdown/text content.")
    return str(text).strip() + "\n"


def main() -> int:
    args = parse_args()
    source = Path(args.file).expanduser().resolve()
    if not source.exists():
        die(f"File not found: {source}")
    if not source.is_file():
        die(f"Not a file: {source}")

    out = (
        Path(args.out).expanduser().resolve()
        if args.out
        else source.with_suffix(source.suffix + ".markitdown.md")
    )

    try:
        markdown = convert_with_markitdown(source)
    except Exception as exc:
        die(f"Conversion failed for {source.name}: {exc}")

    if args.stdout:
        sys.stdout.write(markdown[: max(args.preview_chars, 0)] if args.preview_chars else markdown)
        if args.preview_chars and len(markdown) > args.preview_chars:
            print(
                f"\n[truncated: {len(markdown) - args.preview_chars} more chars in full conversion]",
                file=sys.stderr,
            )
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")

    preview_len = max(args.preview_chars, 0)
    print(f"Converted: {source}")
    print(f"Markdown:  {out}")
    print(f"Chars:     {len(markdown)}")
    print(f"Formats:   {SUPPORTED_HINT}")
    if preview_len:
        print("\n--- preview ---")
        sys.stdout.write(markdown[:preview_len])
        if len(markdown) > preview_len:
            print(f"\n--- truncated: {len(markdown) - preview_len} more chars in {out} ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import html
import json
import re
from pathlib import Path


def parse(path: str, output_dir: str | None = None) -> dict:
    """Format-agnostic entry point. Dispatches on file extension and always
    returns markdown for the Chunker.

    - .pdf            -> docling (layout/tables/OCR)
    - .htm / .html    -> plain text from <pre>/tag-strip + entity unescape
    - anything else   -> read as plain text (.txt and any future text format)

    PDFs carry a structured docling JSON; other formats don't, so `json` is None
    and `ocr_used` is False for them. Adding a new format = one branch here."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(p, output_dir)

    raw = p.read_text(encoding="utf-8")
    if ext in (".htm", ".html"):
        md = _html_to_markdown(raw)
    elif ext == ".md":
        md = raw  # already markdown — don't mangle existing headers
    else:
        md = _promote_headings(raw)  # .txt and unknown text formats

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{p.stem}.md").write_text(md, encoding="utf-8")

    return {"markdown": md, "json": None, "ocr_used": False}


def _parse_pdf(p: Path, output_dir: str | None) -> dict:
    """docling backend: two-pass (no-OCR, then OCR if the text comes back nearly
    empty). docling is imported lazily so text-only runs don't need it."""
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

    def convert(enable_ocr: bool):
        pipeline = PdfPipelineOptions()
        pipeline.do_ocr = enable_ocr
        pipeline.do_table_structure = True
        pipeline.table_structure_options.mode = TableFormerMode.FAST
        return DocumentConverter(
            format_options={"pdf": PdfFormatOption(pipeline_options=pipeline)}
        ).convert(str(p))

    result = convert(enable_ocr=False)
    md = result.document.export_to_markdown()
    ocr_used = False

    if len(md.strip()) < 100:
        result = convert(enable_ocr=True)
        md = result.document.export_to_markdown()
        ocr_used = True

    json_data = result.document.export_to_dict()

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{p.stem}.md").write_text(md, encoding="utf-8")
        with open(out / f"{p.stem}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

    return {"markdown": md, "json": json_data, "ocr_used": ocr_used}


def _html_to_markdown(raw: str) -> str:
    """Pull readable text out of HTML. GPO-style documents wrap their body in a
    single <pre> block of clean plain text; prefer it, else strip all tags."""
    m = re.search(r"<pre[^>]*>(.*?)</pre>", raw, re.S | re.I)
    body = m.group(1) if m else re.sub(r"<[^>]+>", "", raw)
    return _promote_headings(html.unescape(body))


def _promote_headings(text: str) -> str:
    """Recover structure from header-less plain text: lines that look like
    section headings become markdown `#` headers so the Chunker can split on
    them. Generic heuristic (short, all-caps), not tied to any document type."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and _looks_like_heading(s):
            out.append(f"# {s}")
        else:
            out.append(line)
    return "\n".join(out)


def _looks_like_heading(s: str) -> bool:
    # Short, all-caps (has letters), not a sentence (no trailing . , ; :).
    if len(s) > 80 or s.endswith((".", ",", ";", ":")):
        return False
    return any(c.isalpha() for c in s) and s == s.upper()

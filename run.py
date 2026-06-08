import json
import math
import os
from pathlib import Path

from Parser import parse
from Chunker import chunk
from Extractor import extract_chunk, preload
from FundingSchema import FundingExtraction, SYSTEM_PROMPT, funding_tag_fn

input_dir = Path("./data/inputs/")
output_dir = Path("./data/parsed/")
chunks_dir = Path("./data/chunks/")
extracted_dir = Path("./data/extracted/")

# --- Config (set by run.sh / environment) ---
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")  # prod: qwen3.6:27b
THINK = os.environ.get("OLLAMA_THINK", "false").lower() == "true"
OUTPUT_TOKENS = 8192  # headroom reserved for generation on top of the largest input

def _est_tokens(text: str) -> int:
    # Rough char/3 estimate (conservative for dense legislative text).
    return len(text) // 3


def compute_num_ctx(chunk_files: list[Path]) -> int:
    """One constant context size = largest (prompt + chunk) input + output
    headroom. Constant across every call so Ollama loads the model once and
    keeps it resident — changing num_ctx between calls would force a reload."""
    override = os.environ.get("OLLAMA_NUM_CTX")
    if override:
        return int(override)
    prompt_tokens = _est_tokens(SYSTEM_PROMPT)
    max_input = 0
    for cf in chunk_files:
        for ch in json.loads(cf.read_text(encoding="utf-8")):
            max_input = max(max_input, prompt_tokens + _est_tokens(ch.get("content", "")))
    total = max_input + OUTPUT_TOKENS
    # round up to a multiple of 1024, with a sane floor
    return max(8192, math.ceil(total / 1024) * 1024)


# Parse and chunk. Parser dispatches by extension (.pdf via docling, .htm/.html
# and .txt as text); any other extension is skipped here.
SUPPORTED_EXTS = {".pdf", ".htm", ".html", ".txt", ".md"}

for file_path in sorted(input_dir.rglob("*")):
    if file_path.suffix.lower() not in SUPPORTED_EXTS:
        continue
    try:
        result = parse(str(file_path), output_dir=str(output_dir))
        print(f"{file_path.name} -> OCR used: {result['ocr_used']}")

        # PDFs carry reliable docling headers (json present) -> keep sections
        # intact; text formats may hold a huge header-less block -> sub-split.
        chunks = chunk(result["markdown"], split_oversized=result["json"] is None)
        chunks_dir.mkdir(parents=True, exist_ok=True)
        with open(chunks_dir / f"{file_path.stem}.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"  {len(chunks)} chunks")
    except Exception as e:
        print(f"Failed: {file_path}: {e}")

# Extract
chunk_files = sorted(chunks_dir.glob("*.json"))
NUM_CTX = compute_num_ctx(chunk_files)
print(f"\nmodel={MODEL} think={THINK} num_ctx={NUM_CTX} num_predict=-1")
preload(MODEL, SYSTEM_PROMPT, NUM_CTX, THINK)  # warm once; Ollama's default keep-alive holds it for the run

for chunks_path in chunk_files:
    doc_name = chunks_path.stem
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    results = []

    for i, chunk_obj in enumerate(chunks):
        print(f"  {doc_name} chunk {i + 1}/{len(chunks)}: {chunk_obj.get('title', '')[:60]}")
        extraction = extract_chunk(
            chunk_obj, MODEL, SYSTEM_PROMPT, FundingExtraction,
            num_ctx=NUM_CTX, num_predict=-1, think=THINK,
        )
        extraction_dict = extraction.model_dump()

        tags = {
            "doc_name": doc_name,
            "chunk_index": i,
            "chunk_title": chunk_obj.get("title", ""),
            "section_path": chunk_obj.get("breadcrumb", []) + chunk_obj.get("sections", []),
            "section_depth": len(chunk_obj.get("breadcrumb", [])),
            **funding_tag_fn(chunk_obj, extraction_dict),
        }
        results.append({
            "tags": tags,
            "extraction": extraction_dict,
            "title": chunk_obj.get("title"),
            "sections": chunk_obj.get("sections"),
            "breadcrumb": chunk_obj.get("breadcrumb"),
            "content": chunk_obj.get("content"),
        })

    extracted_dir.mkdir(parents=True, exist_ok=True)
    out_path = extracted_dir / f"{doc_name}.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {len(results)} chunks written to {out_path}")

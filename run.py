from pathlib import Path
import json
from PDFParser import parse
from Chunker import chunk

input_dir = Path("./data/inputs/")
output_dir = Path("./data/parsed/")
chunks_dir = Path("./data/chunks/")

for file_path in input_dir.rglob("*.pdf"):
    try:
        result = parse(str(file_path), output_dir=str(output_dir))
        print(f"{file_path.name} -> OCR used: {result['ocr_used']}")

        chunks = chunk(result["markdown"])
        chunks_dir.mkdir(parents=True, exist_ok=True)
        with open(chunks_dir / f"{file_path.stem}.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"  {len(chunks)} chunks")
    except Exception as e:
        print(f"Failed: {file_path}: {e}")

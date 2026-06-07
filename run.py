from pathlib import Path
from PDFParser import parse

input_dir = Path("./data/inputs/")
output_dir = Path("./data/parsed/")

for file_path in input_dir.rglob("*.pdf"):
    try:
        result = parse(str(file_path), output_dir=str(output_dir))
        print(f"{file_path.name} -> OCR used: {result['ocr_used']}")
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
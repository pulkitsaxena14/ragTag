from pathlib import Path
from PDFParser import PDFParser


def parse_directory(input_dir: str, output_dir: str, pattern: str = "*.pdf"):
    """
    Recursively parse all matching files in a directory using PDFParser.
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    parser = PDFParser()
    results = []

    # recursively match files (use rglob for subdirectories)
    for file_path in input_path.rglob(pattern):
        if not file_path.is_file():
            continue

        try:
            result = parser.parse(
                str(file_path),
                output_dir=str(output_path),
            )

            print(f"{file_path.name} -> OCR used: {result.get('ocr_used')}")
            results.append((file_path, result))

        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")

    return results


# usage
results = parse_directory(
    input_dir="./data/inputs/",
    output_dir="./data/parsed/"
)
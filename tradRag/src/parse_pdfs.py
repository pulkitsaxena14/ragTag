from pathlib import Path

from docling.document_converter import DocumentConverter

from config import PDF_DIR, PARSED_DIR


def parse_pdfs():

    converter = DocumentConverter()

    pdf_dir = Path(PDF_DIR)
    parsed_dir = Path(PARSED_DIR)

    parsed_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_dir.glob("*.pdf"):

        print(f"Parsing {pdf_file.name}")

        result = converter.convert(str(pdf_file))

        markdown = result.document.export_to_markdown()

        output_file = parsed_dir / f"{pdf_file.stem}.md"

        output_file.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    parse_pdfs()

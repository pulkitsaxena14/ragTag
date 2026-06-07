from pathlib import Path
import json

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode


def parse(pdf_path: str, output_dir: str | None = None):
    pdf_path = Path(pdf_path)

    def convert(enable_ocr: bool):
        pipeline = PdfPipelineOptions()
        pipeline.do_ocr = enable_ocr
        pipeline.do_table_structure = True
        pipeline.table_structure_options.mode = TableFormerMode.FAST
        return DocumentConverter(
            format_options={"pdf": PdfFormatOption(pipeline_options=pipeline)}
        ).convert(str(pdf_path))

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
        stem = pdf_path.stem
        (out / f"{stem}.md").write_text(md, encoding="utf-8")
        with open(out / f"{stem}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

    return {"markdown": md, "json": json_data, "ocr_used": ocr_used}

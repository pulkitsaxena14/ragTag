from pathlib import Path
import json

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)

class PDFParser:
    def __init__(self):
        pass

    def parse(
        self,
        pdf_path: str,
        output_dir: str | None = None,
    ):
        pdf_path = Path(pdf_path)

        # TODO: Add heirarchy aware section parsing; currently absent from docling
        try:
            result = self._convert(
                pdf_path,
                enable_ocr=False,
            )

            # Simple quality check
            md = result.document.export_to_markdown()

            if len(md.strip()) < 100:
                raise ValueError(
                    "Too little text extracted"
                )

            ocr_used = False

        except Exception:
            result = self._convert(
                pdf_path,
                enable_ocr=True,
            )

            md = result.document.export_to_markdown()
            ocr_used = True

        json_data = result.document.export_to_dict()

        if output_dir:
            self._export(
                pdf_path,
                output_dir,
                md,
                json_data,
            )

        return {
            "markdown": md,
            "json": json_data,
            "ocr_used": ocr_used,
        }

    def _convert(
        self,
        pdf_path: Path,
        enable_ocr: bool,
    ):
        pipeline = PdfPipelineOptions()

        pipeline.do_ocr = enable_ocr

        # Fast table extraction
        pipeline.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(
                    pipeline_options=pipeline
                )
            }
        )

        return converter.convert(str(pdf_path))

    def _export(
        self,
        pdf_path,
        output_dir,
        markdown,
        json_data,
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        stem = pdf_path.stem

        md_file = output_dir / f"{stem}.md"
        json_file = output_dir / f"{stem}.json"

        md_file.write_text(
            markdown,
            encoding="utf-8",
        )

        with open(
            json_file,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                json_data,
                f,
                indent=2,
                ensure_ascii=False,
            )
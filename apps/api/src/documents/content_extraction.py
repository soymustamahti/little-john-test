import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile

import openpyxl
import xlrd
from pypdf import PdfReader

from src.documents.ocr import OpenAIDocumentOcrClient
from src.documents.processing_schemas import ExtractedDocumentContent

DOCX_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
ODS_TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
ODS_TEXT_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".ods", ".csv"}


class ContentExtractionError(Exception):
    pass


class DocumentContentExtractor:
    def __init__(
        self,
        *,
        ocr_client: OpenAIDocumentOcrClient,
        pdf_direct_text_min_characters: int,
        pdf_direct_text_min_average_characters_per_page: int,
    ) -> None:
        self._ocr_client = ocr_client
        self._pdf_direct_text_min_characters = pdf_direct_text_min_characters
        self._pdf_direct_text_min_average_characters_per_page = (
            pdf_direct_text_min_average_characters_per_page
        )

    async def extract_content(
        self,
        *,
        filename: str,
        file_extension: str,
        content_type: str,
        content: bytes,
    ) -> ExtractedDocumentContent:
        if file_extension in IMAGE_EXTENSIONS:
            text = await self._ocr_client.extract_text_from_image(
                content=content,
                content_type=content_type,
            )
            return self._build_result(
                text=text,
                content_source="image_ocr",
                metadata={
                    "ocr_provider": self._ocr_client.provider_name,
                    "ocr_model": self._ocr_client.model_name,
                },
            )

        if file_extension == ".pdf":
            return await self._extract_pdf_content(filename=filename, content=content)

        if file_extension == ".docx":
            return self._build_result(
                text=self._extract_docx_text(content),
                content_source="docx_xml",
                metadata={},
            )

        if file_extension in SPREADSHEET_EXTENSIONS:
            return self._build_result(
                text=self._extract_spreadsheet_text(file_extension=file_extension, content=content),
                content_source="spreadsheet_cells",
                metadata={"file_extension": file_extension},
            )

        raise ContentExtractionError(f"Unsupported extraction file type: {file_extension}.")

    async def _extract_pdf_content(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> ExtractedDocumentContent:
        page_texts, page_count = self._extract_pdf_text_pages(content)
        direct_text = "\n\n".join(text for text in page_texts if text)
        direct_text_character_count = len(self._strip_whitespace(direct_text))
        average_characters_per_page = (
            direct_text_character_count / page_count if page_count else 0
        )

        if (
            direct_text_character_count >= self._pdf_direct_text_min_characters
            and average_characters_per_page
            >= self._pdf_direct_text_min_average_characters_per_page
        ):
            return self._build_result(
                text=direct_text,
                content_source="pdf_text",
                metadata={
                    "page_count": page_count,
                    "direct_text_character_count": direct_text_character_count,
                    "average_characters_per_page": average_characters_per_page,
                    "ocr_used": False,
                },
            )

        ocr_text = await self._ocr_client.extract_text_from_pdf(
            content=content,
            filename=filename,
        )

        return self._build_result(
            text=ocr_text,
            content_source="pdf_ocr",
            metadata={
                "page_count": page_count,
                "direct_text_character_count": direct_text_character_count,
                "average_characters_per_page": average_characters_per_page,
                "ocr_used": True,
                "ocr_provider": self._ocr_client.provider_name,
                "ocr_model": self._ocr_client.model_name,
            },
        )

    @staticmethod
    def _extract_pdf_text_pages(content: bytes) -> tuple[list[str], int]:
        try:
            reader = PdfReader(io.BytesIO(content))
        except Exception:
            return [], 0

        page_texts = [
            DocumentContentExtractor._normalize_text(page.extract_text() or "")
            for page in reader.pages
        ]
        return page_texts, len(page_texts)

    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml_bytes = archive.read("word/document.xml")
        except (KeyError, zipfile.BadZipFile) as exc:
            raise ContentExtractionError("Unable to extract text from DOCX file.") from exc

        root = ET.fromstring(xml_bytes)
        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:body/w:p", DOCX_NAMESPACE):
            parts = [node.text for node in paragraph.findall(".//w:t", DOCX_NAMESPACE) if node.text]
            paragraph_text = "".join(parts).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)
        return "\n\n".join(paragraphs)

    @staticmethod
    def _extract_spreadsheet_text(*, file_extension: str, content: bytes) -> str:
        if file_extension == ".csv":
            try:
                return DocumentContentExtractor._extract_csv_text(content)
            except UnicodeDecodeError as exc:
                raise ContentExtractionError("Unable to decode CSV file.") from exc
        if file_extension == ".xlsx":
            return DocumentContentExtractor._extract_xlsx_text(content)
        if file_extension == ".xls":
            return DocumentContentExtractor._extract_xls_text(content)
        if file_extension == ".ods":
            return DocumentContentExtractor._extract_ods_text(content)
        raise ContentExtractionError(f"Unsupported spreadsheet file type: {file_extension}.")

    @staticmethod
    def _extract_csv_text(content: bytes) -> str:
        text = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        return "\n".join(",".join(cell.strip() for cell in row) for row in reader)

    @staticmethod
    def _extract_xlsx_text(content: bytes) -> str:
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except Exception as exc:
            raise ContentExtractionError("Unable to extract text from XLSX file.") from exc

        try:
            lines: list[str] = []
            for worksheet in workbook.worksheets:
                lines.extend(DocumentContentExtractor._sheet_header_lines(worksheet.title))
                for row in worksheet.iter_rows(values_only=True):
                    rendered_row = DocumentContentExtractor._render_row(row)
                    if rendered_row:
                        lines.append(rendered_row)
            return "\n".join(lines)
        finally:
            workbook.close()

    @staticmethod
    def _extract_xls_text(content: bytes) -> str:
        try:
            workbook = xlrd.open_workbook(file_contents=content)
        except Exception as exc:
            raise ContentExtractionError("Unable to extract text from XLS file.") from exc

        lines: list[str] = []
        for sheet in workbook.sheets():
            lines.extend(DocumentContentExtractor._sheet_header_lines(sheet.name))
            for row_index in range(sheet.nrows):
                rendered_row = DocumentContentExtractor._render_row(sheet.row_values(row_index))
                if rendered_row:
                    lines.append(rendered_row)
        return "\n".join(lines)

    @staticmethod
    def _extract_ods_text(content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml_bytes = archive.read("content.xml")
        except (KeyError, zipfile.BadZipFile) as exc:
            raise ContentExtractionError("Unable to extract text from ODS file.") from exc

        root = ET.fromstring(xml_bytes)
        lines: list[str] = []
        table_tag = f"{{{ODS_TABLE_NAMESPACE}}}table"
        row_tag = f"{{{ODS_TABLE_NAMESPACE}}}table-row"
        cell_tag = f"{{{ODS_TABLE_NAMESPACE}}}table-cell"
        text_tag = f"{{{ODS_TEXT_NAMESPACE}}}p"

        for table in root.iter(table_tag):
            table_name = table.attrib.get(f"{{{ODS_TABLE_NAMESPACE}}}name", "Sheet")
            lines.extend(DocumentContentExtractor._sheet_header_lines(table_name))
            for row in table.findall(row_tag):
                values: list[str] = []
                for cell in row.findall(cell_tag):
                    texts = [node.text or "" for node in cell.findall(text_tag)]
                    values.append(" ".join(text.strip() for text in texts if text.strip()))
                rendered_row = DocumentContentExtractor._render_row(values)
                if rendered_row:
                    lines.append(rendered_row)
        return "\n".join(lines)

    @staticmethod
    def _build_result(
        *,
        text: str,
        content_source: str,
        metadata: dict,
    ) -> ExtractedDocumentContent:
        normalized_text = DocumentContentExtractor._normalize_text(text)
        if not normalized_text:
            raise ContentExtractionError("No extractable text was produced for this document.")

        final_metadata = {
            **metadata,
            "character_count": len(normalized_text),
        }
        return ExtractedDocumentContent(
            text=normalized_text,
            content_source=content_source,
            metadata=final_metadata,
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
        return "\n".join(line for line in normalized_lines if line).strip()

    @staticmethod
    def _strip_whitespace(value: str) -> str:
        return re.sub(r"\s+", "", value)

    @staticmethod
    def _render_row(row: list | tuple) -> str:
        values = [str(value).strip() for value in row if value not in (None, "")]
        return " | ".join(values)

    @staticmethod
    def _sheet_header_lines(sheet_name: str) -> list[str]:
        return [f"# Sheet: {sheet_name}"]

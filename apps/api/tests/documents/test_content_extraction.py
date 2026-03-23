import io
import zipfile

import openpyxl
import pytest
from pypdf import PdfWriter
from src.documents.content_extraction import DocumentContentExtractor
from src.documents.processing import DocumentProcessingService


class FakeOcrClient:
    provider_name = "openai"
    model_name = "gpt-4o"

    def __init__(self) -> None:
        self.image_calls = 0
        self.pdf_calls = 0

    async def extract_text_from_image(self, *, content: bytes, content_type: str) -> str:
        self.image_calls += 1
        return "image line 1\nimage line 2"

    async def extract_text_from_pdf(self, *, content: bytes, filename: str) -> str:
        self.pdf_calls += 1
        return "pdf ocr text"


class FakeChunker:
    def chunk_text(self, text: str) -> list[tuple[str, int, int]]:
        return [(text, 0, len(text))]


class FakeEmbeddingClient:
    provider_name = "openai"
    model_name = "text-embedding-3-small"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def build_docx_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>"
                "</w:document>"
            ),
        )
    return buffer.getvalue()


def build_xlsx_bytes() -> bytes:
    buffer = io.BytesIO()
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Invoices"
    worksheet.append(["invoice_number", "amount"])
    worksheet.append(["INV-001", 1200])
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def build_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_extract_content_uses_ocr_for_images() -> None:
    ocr_client = FakeOcrClient()
    extractor = DocumentContentExtractor(
        ocr_client=ocr_client,
        pdf_direct_text_min_characters=120,
        pdf_direct_text_min_average_characters_per_page=60,
    )

    result = await extractor.extract_content(
        filename="scan.png",
        file_extension=".png",
        content_type="image/png",
        content=b"\x89PNG\r\n\x1a\nfake",
    )

    assert result.content_source == "image_ocr"
    assert "image line 1" in result.text
    assert ocr_client.image_calls == 1


@pytest.mark.asyncio
async def test_extract_content_falls_back_to_ocr_for_low_text_pdf() -> None:
    ocr_client = FakeOcrClient()
    extractor = DocumentContentExtractor(
        ocr_client=ocr_client,
        pdf_direct_text_min_characters=120,
        pdf_direct_text_min_average_characters_per_page=60,
    )

    result = await extractor.extract_content(
        filename="scan.pdf",
        file_extension=".pdf",
        content_type="application/pdf",
        content=build_blank_pdf_bytes(),
    )

    assert result.content_source == "pdf_ocr"
    assert result.text == "pdf ocr text"
    assert ocr_client.pdf_calls == 1


@pytest.mark.asyncio
async def test_extract_content_reads_docx_text_locally() -> None:
    extractor = DocumentContentExtractor(
        ocr_client=FakeOcrClient(),
        pdf_direct_text_min_characters=120,
        pdf_direct_text_min_average_characters_per_page=60,
    )

    result = await extractor.extract_content(
        filename="contract.docx",
        file_extension=".docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        content=build_docx_bytes("Supplier Agreement"),
    )

    assert result.content_source == "docx_xml"
    assert result.text == "Supplier Agreement"


@pytest.mark.asyncio
async def test_extract_content_reads_xlsx_text_locally() -> None:
    extractor = DocumentContentExtractor(
        ocr_client=FakeOcrClient(),
        pdf_direct_text_min_characters=120,
        pdf_direct_text_min_average_characters_per_page=60,
    )

    result = await extractor.extract_content(
        filename="invoices.xlsx",
        file_extension=".xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=build_xlsx_bytes(),
    )

    assert result.content_source == "spreadsheet_cells"
    assert "# Sheet: Invoices" in result.text
    assert "INV-001 | 1200" in result.text


@pytest.mark.asyncio
async def test_processing_service_chunks_and_embeds_extracted_text() -> None:
    extractor = DocumentContentExtractor(
        ocr_client=FakeOcrClient(),
        pdf_direct_text_min_characters=120,
        pdf_direct_text_min_average_characters_per_page=60,
    )
    service = DocumentProcessingService(
        extractor=extractor,
        chunker=FakeChunker(),
        embedding_client=FakeEmbeddingClient(),
    )

    result = await service.process_document(
        filename="contract.docx",
        file_extension=".docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        content=build_docx_bytes("Supplier Agreement"),
    )

    assert result.content_source == "docx_xml"
    assert result.metadata["chunk_count"] == 1
    assert result.metadata["embedding_model"] == "text-embedding-3-small"
    assert result.chunks[0].embedding == [0.1, 0.2, 0.3]

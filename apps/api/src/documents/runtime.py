from functools import lru_cache

from src.core.config import get_settings
from src.documents.chunking import DocumentTextChunker
from src.documents.content_extraction import DocumentContentExtractor
from src.documents.embeddings import OpenAIEmbeddingClient
from src.documents.ocr import OpenAIDocumentOcrClient
from src.documents.processing import DocumentProcessingService


@lru_cache
def get_document_processing_service() -> DocumentProcessingService:
    settings = get_settings()
    extractor = DocumentContentExtractor(
        ocr_client=OpenAIDocumentOcrClient(settings.openai_provider),
        pdf_direct_text_min_characters=settings.documents.pdf_direct_text_min_characters,
        pdf_direct_text_min_average_characters_per_page=(
            settings.documents.pdf_direct_text_min_average_characters_per_page
        ),
    )
    chunker = DocumentTextChunker(
        chunk_size=settings.documents.chunk_max_characters,
        min_characters_per_chunk=settings.documents.chunk_min_characters,
    )
    embedding_client = OpenAIEmbeddingClient(settings.openai_provider)
    return DocumentProcessingService(
        extractor=extractor,
        chunker=chunker,
        embedding_client=embedding_client,
    )

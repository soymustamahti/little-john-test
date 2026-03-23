from functools import lru_cache

from src.core.config import get_settings
from src.core.database import get_async_session_factory
from src.documents.chunking import DocumentTextChunker
from src.documents.content_extraction import DocumentContentExtractor
from src.documents.embeddings import OpenAIEmbeddingClient
from src.documents.extraction_service import DocumentExtractionService
from src.documents.ocr import OpenAIDocumentOcrClient
from src.documents.processing import DocumentProcessingService
from src.documents.reranking import build_document_reranker
from src.documents.retrieval import DocumentRetrievalService
from src.storage.r2 import R2ObjectStorage


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


@lru_cache
def get_r2_object_storage() -> R2ObjectStorage:
    settings = get_settings()
    return R2ObjectStorage(settings.r2)


@lru_cache
def get_document_retrieval_service() -> DocumentRetrievalService:
    settings = get_settings()
    return DocumentRetrievalService(
        get_async_session_factory(),
        get_r2_object_storage(),
        OpenAIEmbeddingClient(settings.openai_provider),
        build_document_reranker(settings.openai_provider),
        settings.documents.hybrid_candidate_pool_size,
    )


@lru_cache
def get_document_extraction_service() -> DocumentExtractionService:
    return DocumentExtractionService(get_async_session_factory())

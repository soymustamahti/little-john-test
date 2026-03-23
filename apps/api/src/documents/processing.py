from src.documents.chunking import DocumentTextChunker
from src.documents.content_extraction import ContentExtractionError, DocumentContentExtractor
from src.documents.embeddings import EmbeddingError, OpenAIEmbeddingClient
from src.documents.ocr import OcrError
from src.documents.processing_schemas import ChunkEmbedding, ProcessedDocumentContent


class DocumentProcessingError(Exception):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DocumentProcessingService:
    def __init__(
        self,
        *,
        extractor: DocumentContentExtractor,
        chunker: DocumentTextChunker,
        embedding_client: OpenAIEmbeddingClient,
    ) -> None:
        self._extractor = extractor
        self._chunker = chunker
        self._embedding_client = embedding_client

    async def process_document(
        self,
        *,
        filename: str,
        file_extension: str,
        content_type: str,
        content: bytes,
    ) -> ProcessedDocumentContent:
        try:
            extracted = await self._extractor.extract_content(
                filename=filename,
                file_extension=file_extension,
                content_type=content_type,
                content=content,
            )
        except OcrError as exc:
            raise DocumentProcessingError(str(exc), status_code=503) from exc
        except ContentExtractionError as exc:
            raise DocumentProcessingError(str(exc), status_code=422) from exc

        chunk_specs = self._chunker.chunk_text(extracted.text)
        if not chunk_specs:
            raise DocumentProcessingError(
                "Document extraction produced no chunkable text.",
                status_code=422,
            )

        texts = [chunk_text for chunk_text, _, _ in chunk_specs]
        try:
            embeddings = await self._embedding_client.embed_texts(texts)
        except EmbeddingError as exc:
            raise DocumentProcessingError(str(exc), status_code=503) from exc

        chunks = [
            ChunkEmbedding(
                chunk_index=index,
                content=chunk_text,
                content_start_offset=start_offset,
                content_end_offset=end_offset,
                embedding=embedding,
            )
            for index, ((chunk_text, start_offset, end_offset), embedding) in enumerate(
                zip(chunk_specs, embeddings, strict=True)
            )
        ]

        metadata = {
            **extracted.metadata,
            "chunk_count": len(chunks),
            "embedding_provider": self._embedding_client.provider_name,
            "embedding_model": self._embedding_client.model_name,
        }
        return ProcessedDocumentContent(
            text=extracted.text,
            content_source=extracted.content_source,
            metadata=metadata,
            chunks=chunks,
        )

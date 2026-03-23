from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedDocumentContent:
    text: str
    content_source: str
    metadata: dict


@dataclass(frozen=True)
class ChunkEmbedding:
    chunk_index: int
    content: str
    content_start_offset: int
    content_end_offset: int
    embedding: list[float]


@dataclass(frozen=True)
class ProcessedDocumentContent:
    text: str
    content_source: str
    metadata: dict
    chunks: list[ChunkEmbedding]

from __future__ import annotations

import io
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import HTTPException, status

from src.core.database import AsyncSession, async_sessionmaker
from src.documents.embeddings import OpenAIEmbeddingClient
from src.documents.model import DocumentChunkModel
from src.documents.repository import DocumentRepository
from src.documents.reranking import (
    DocumentReranker,
    RerankCandidate,
    RerankerUnavailableError,
)
from src.storage.object_store import ObjectStorage, ObjectStorageError

try:
    import pandas as pd
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    pd = None


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_index: int
    score: float
    match_type: str
    excerpt: str


class ChunkLike(Protocol):
    chunk_index: int
    content: str
    embedding: list[float]


@dataclass(frozen=True)
class _HybridCandidate:
    chunk_index: int
    content: str
    excerpt: str
    keyword_score: float | None
    semantic_score: float | None
    match_type: str


class DocumentRetrievalService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        object_storage: ObjectStorage,
        embedding_client: OpenAIEmbeddingClient,
        reranker: DocumentReranker | None = None,
        hybrid_candidate_pool_size: int = 10,
    ) -> None:
        self._session_factory = session_factory
        self._object_storage = object_storage
        self._embedding_client = embedding_client
        self._reranker = reranker
        self._hybrid_candidate_pool_size = max(2, hybrid_candidate_pool_size)

    async def keyword_search(
        self,
        *,
        document_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        chunks = await self._load_chunks(document_id)
        return self._keyword_search_chunks(chunks=chunks, query=query, top_k=top_k)

    async def semantic_search(
        self,
        *,
        document_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        chunks = await self._load_chunks(document_id)
        if not chunks:
            return []

        query_vector = await self._embed_query(query)
        if query_vector is None:
            return []
        return self._semantic_search_chunks(
            chunks=chunks,
            query_vector=query_vector,
            top_k=top_k,
        )

    async def hybrid_search(
        self,
        *,
        document_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        chunks = await self._load_chunks(document_id)
        if not chunks:
            return []

        candidate_pool_size = max(top_k, min(self._hybrid_candidate_pool_size, 24))
        keyword_results = self._keyword_search_chunks(
            chunks=chunks,
            query=query,
            top_k=candidate_pool_size,
        )
        query_vector = await self._embed_query(query)
        semantic_results = (
            self._semantic_search_chunks(
                chunks=chunks,
                query_vector=query_vector,
                top_k=candidate_pool_size,
            )
            if query_vector is not None
            else []
        )

        chunks_by_index = {chunk.chunk_index: chunk for chunk in chunks}
        merged: dict[int, _HybridCandidate] = {}
        for result in keyword_results:
            chunk = chunks_by_index.get(result.chunk_index)
            if chunk is None:
                continue
            merged[result.chunk_index] = _HybridCandidate(
                chunk_index=result.chunk_index,
                content=chunk.content,
                excerpt=result.excerpt,
                keyword_score=result.score,
                semantic_score=None,
                match_type=result.match_type,
            )

        for result in semantic_results:
            previous = merged.get(result.chunk_index)
            if previous is None:
                chunk = chunks_by_index.get(result.chunk_index)
                if chunk is None:
                    continue
                merged[result.chunk_index] = _HybridCandidate(
                    chunk_index=result.chunk_index,
                    content=chunk.content,
                    excerpt=result.excerpt,
                    keyword_score=None,
                    semantic_score=result.score,
                    match_type=result.match_type,
                )
                continue

            merged[result.chunk_index] = _HybridCandidate(
                chunk_index=result.chunk_index,
                content=previous.content,
                keyword_score=previous.keyword_score,
                semantic_score=result.score,
                match_type="hybrid",
                excerpt=(
                    previous.excerpt
                    if len(previous.excerpt) >= len(result.excerpt)
                    else result.excerpt
                ),
            )

        candidates = list(merged.values())
        reranked = await self._rerank_hybrid_candidates(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )
        if reranked is not None:
            return reranked

        return self._fallback_rank_hybrid_candidates(
            candidates=candidates,
            keyword_results=keyword_results,
            semantic_results=semantic_results,
            top_k=top_k,
        )

    async def inspect_chunk(
        self,
        *,
        document_id: UUID,
        chunk_index: int,
    ) -> RetrievedChunk:
        chunks = await self._load_chunks(document_id)
        for chunk in chunks:
            if chunk.chunk_index == chunk_index:
                return RetrievedChunk(
                    chunk_index=chunk.chunk_index,
                    score=1,
                    match_type="inspection",
                    excerpt=_build_excerpt(chunk.content, max_characters=1_500),
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk {chunk_index} was not found for document {document_id}.",
        )

    async def inspect_spreadsheet(
        self,
        *,
        document_id: UUID,
        sheet_name: str | None = None,
        max_rows: int = 20,
    ) -> dict[str, object]:
        if pd is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Pandas is required for spreadsheet inspection.",
            )

        async with self._session_factory() as session:
            repository = DocumentRepository(session)
            document = await repository.get(document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} was not found.",
                )

        if document.file_kind != "spreadsheet":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Spreadsheet inspection is only available for spreadsheet documents.",
            )

        try:
            stored_object = await self._object_storage.download_object(key=document.storage_key)
        except ObjectStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        buffer = io.BytesIO(stored_object.content)
        file_extension = document.file_extension.lower()

        if file_extension == ".csv":
            frame = pd.read_csv(buffer)
            preview = frame.head(max_rows).fillna("").to_dict(orient="records")
            return {
                "sheet_name": "CSV",
                "columns": [str(column) for column in frame.columns.tolist()],
                "rows": preview,
            }

        workbook = pd.read_excel(buffer, sheet_name=None)
        if not workbook:
            return {"sheet_name": sheet_name or "Sheet1", "columns": [], "rows": []}

        selected_sheet_name = sheet_name or next(iter(workbook.keys()))
        frame = workbook.get(selected_sheet_name)
        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sheet '{selected_sheet_name}' was not found in document {document_id}.",
            )

        normalized = frame.head(max_rows).fillna("")
        return {
            "sheet_name": selected_sheet_name,
            "columns": [str(column) for column in normalized.columns.tolist()],
            "rows": normalized.to_dict(orient="records"),
        }

    async def _load_chunks(self, document_id: UUID) -> Sequence[DocumentChunkModel]:
        async with self._session_factory() as session:
            repository = DocumentRepository(session)
            document = await repository.get_for_extraction(document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} was not found.",
                )
            return tuple(document.chunks)

    async def _embed_query(self, query: str) -> list[float] | None:
        query_embedding = await self._embedding_client.embed_texts([query])
        if not query_embedding:
            return None
        return query_embedding[0]

    def _keyword_search_chunks(
        self,
        *,
        chunks: Sequence[ChunkLike],
        query: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        ranked: list[tuple[float, ChunkLike]] = []
        for chunk in chunks:
            content = chunk.content.strip()
            if not content:
                continue

            content_tokens = _tokenize(content)
            if not content_tokens:
                continue

            overlap_count = len(query_tokens & content_tokens)
            if overlap_count <= 0:
                continue

            score = overlap_count / len(query_tokens)
            if query.lower() in content.lower():
                score += 0.25
            ranked.append((score, chunk))

        return [
            RetrievedChunk(
                chunk_index=chunk.chunk_index,
                score=score,
                match_type="keyword",
                excerpt=_build_excerpt(chunk.content),
            )
            for score, chunk in sorted(ranked, key=lambda item: item[0], reverse=True)[:top_k]
        ]

    def _semantic_search_chunks(
        self,
        *,
        chunks: Sequence[ChunkLike],
        query_vector: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        ranked: list[tuple[float, ChunkLike]] = []
        for chunk in chunks:
            score = _cosine_similarity(query_vector, chunk.embedding)
            if score <= 0:
                continue
            ranked.append((score, chunk))

        return [
            RetrievedChunk(
                chunk_index=chunk.chunk_index,
                score=score,
                match_type="semantic",
                excerpt=_build_excerpt(chunk.content),
            )
            for score, chunk in sorted(ranked, key=lambda item: item[0], reverse=True)[:top_k]
        ]

    async def _rerank_hybrid_candidates(
        self,
        *,
        query: str,
        candidates: Sequence[_HybridCandidate],
        top_k: int,
    ) -> list[RetrievedChunk] | None:
        if self._reranker is None or not candidates:
            return None

        try:
            reranked = await self._reranker.rerank(
                query=query,
                candidates=[
                    RerankCandidate(
                        chunk_index=candidate.chunk_index,
                        content=candidate.content,
                        excerpt=candidate.excerpt,
                    )
                    for candidate in candidates
                ],
                top_k=top_k,
            )
        except RerankerUnavailableError:
            return None

        match_types = {candidate.chunk_index: candidate.match_type for candidate in candidates}
        return [
            RetrievedChunk(
                chunk_index=item.chunk_index,
                score=item.score,
                match_type=(
                    "hybrid"
                    if match_types.get(item.chunk_index) in {"keyword", "semantic", "hybrid"}
                    else match_types.get(item.chunk_index, "hybrid")
                ),
                excerpt=item.excerpt,
            )
            for item in reranked
        ]

    def _fallback_rank_hybrid_candidates(
        self,
        *,
        candidates: Sequence[_HybridCandidate],
        keyword_results: Sequence[RetrievedChunk],
        semantic_results: Sequence[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        keyword_ranks = {
            result.chunk_index: rank for rank, result in enumerate(keyword_results, start=1)
        }
        semantic_ranks = {
            result.chunk_index: rank for rank, result in enumerate(semantic_results, start=1)
        }

        ranked: list[RetrievedChunk] = []
        for candidate in candidates:
            score = 0.0
            keyword_rank = keyword_ranks.get(candidate.chunk_index)
            semantic_rank = semantic_ranks.get(candidate.chunk_index)

            if keyword_rank is not None:
                score += 1 / (60 + keyword_rank)
            if semantic_rank is not None:
                score += 1 / (60 + semantic_rank)

            if candidate.keyword_score is not None:
                score += candidate.keyword_score * 0.15
            if candidate.semantic_score is not None:
                score += candidate.semantic_score * 0.15

            ranked.append(
                RetrievedChunk(
                    chunk_index=candidate.chunk_index,
                    score=score,
                    match_type=(
                        "hybrid"
                        if candidate.keyword_score is not None
                        and candidate.semantic_score is not None
                        else candidate.match_type
                    ),
                    excerpt=candidate.excerpt,
                )
            )

        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]


def _tokenize(value: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(value.lower()))


def _build_excerpt(value: str, *, max_characters: int = 320) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= max_characters:
        return normalized
    return f"{normalized[: max_characters - 3].rstrip()}..."


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0

    numerator = sum(l_value * r_value for l_value, r_value in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0
    return numerator / (left_norm * right_norm)

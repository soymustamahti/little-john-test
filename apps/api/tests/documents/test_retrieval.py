from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import pytest
from src.documents.reranking import (
    DocumentReranker,
    RerankCandidate,
    RerankedCandidate,
    RerankerUnavailableError,
)
from src.documents.retrieval import DocumentRetrievalService


@dataclass(frozen=True)
class FakeChunk:
    chunk_index: int
    content: str
    embedding: list[float]


class FakeEmbeddingClient:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [list(self._vector) for _ in texts]


class StubRetrievalService(DocumentRetrievalService):
    def __init__(
        self,
        *,
        chunks: Sequence[FakeChunk],
        embedding_vector: list[float],
        reranker: DocumentReranker | None = None,
    ) -> None:
        super().__init__(
            session_factory=cast(Any, object()),
            object_storage=cast(Any, object()),
            embedding_client=FakeEmbeddingClient(embedding_vector),
            reranker=reranker,
            hybrid_candidate_pool_size=6,
        )
        self._chunks = tuple(chunks)

    async def _load_chunks(self, document_id: UUID) -> Sequence[FakeChunk]:
        return self._chunks


class FixedOrderReranker:
    async def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[RerankCandidate],
        top_k: int,
    ) -> list[RerankedCandidate]:
        ordered = sorted(candidates, key=lambda item: item.chunk_index, reverse=True)
        return [
            RerankedCandidate(
                chunk_index=candidate.chunk_index,
                score=1 - (index * 0.1),
                excerpt=candidate.excerpt,
            )
            for index, candidate in enumerate(ordered[:top_k])
        ]


class UnavailableReranker:
    async def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[RerankCandidate],
        top_k: int,
    ) -> list[RerankedCandidate]:
        raise RerankerUnavailableError("reranker is unavailable")


def build_chunks() -> list[FakeChunk]:
    return [
        FakeChunk(
            chunk_index=0,
            content="Enterprise address at 12 Rue des Fleurs Bordeaux.",
            embedding=[0.8, 0.0],
        ),
        FakeChunk(
            chunk_index=1,
            content="Registered office location for the organization.",
            embedding=[1.0, 0.0],
        ),
    ]


@pytest.mark.asyncio
async def test_keyword_and_semantic_search_remain_available() -> None:
    service = StubRetrievalService(
        chunks=build_chunks(),
        embedding_vector=[1.0, 0.0],
    )

    keyword_results = await service.keyword_search(
        document_id=UUID("00000000-0000-0000-0000-000000000001"),
        query="enterprise address bordeaux",
        top_k=2,
    )
    semantic_results = await service.semantic_search(
        document_id=UUID("00000000-0000-0000-0000-000000000001"),
        query="where is the registered office",
        top_k=2,
    )

    assert keyword_results[0].match_type == "keyword"
    assert semantic_results[0].match_type == "semantic"


@pytest.mark.asyncio
async def test_hybrid_search_uses_reranker_order_when_available() -> None:
    service = StubRetrievalService(
        chunks=build_chunks(),
        embedding_vector=[1.0, 0.0],
        reranker=FixedOrderReranker(),
    )

    results = await service.hybrid_search(
        document_id=UUID("00000000-0000-0000-0000-000000000001"),
        query="enterprise address bordeaux",
        top_k=2,
    )

    assert [result.chunk_index for result in results] == [1, 0]
    assert all(result.match_type == "hybrid" for result in results)


@pytest.mark.asyncio
async def test_hybrid_search_falls_back_to_fused_ranking_when_reranker_fails() -> None:
    service = StubRetrievalService(
        chunks=build_chunks(),
        embedding_vector=[1.0, 0.0],
        reranker=UnavailableReranker(),
    )

    results = await service.hybrid_search(
        document_id=UUID("00000000-0000-0000-0000-000000000001"),
        query="enterprise address bordeaux",
        top_k=2,
    )

    assert results[0].chunk_index == 0
    assert results[0].match_type == "hybrid"

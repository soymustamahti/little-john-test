from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


class RerankerUnavailableError(RuntimeError):
    """Raised when the configured reranker cannot be loaded or executed."""


@dataclass(frozen=True)
class RerankCandidate:
    chunk_index: int
    content: str
    excerpt: str


@dataclass(frozen=True)
class RerankedCandidate:
    chunk_index: int
    score: float
    excerpt: str


class DocumentReranker(Protocol):
    async def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[RerankCandidate],
        top_k: int,
        ) -> list[RerankedCandidate]:
        ...


class CrossEncoderLike(Protocol):
    def predict(
        self,
        sentences: Sequence[tuple[str, str]],
    ) -> Sequence[float]:
        ...


class CrossEncoderDocumentReranker:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    async def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[RerankCandidate],
        top_k: int,
    ) -> list[RerankedCandidate]:
        if not candidates:
            return []

        try:
            model = await asyncio.to_thread(_load_cross_encoder, self._model_name)
            scores = await asyncio.to_thread(
                model.predict,
                [(query, candidate.content) for candidate in candidates],
            )
        except Exception as exc:  # pragma: no cover - depends on optional runtime deps
            raise RerankerUnavailableError(
                f"Cross-encoder reranking is unavailable for '{self._model_name}'."
            ) from exc

        ranked = sorted(
            zip(candidates, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        return [
            RerankedCandidate(
                chunk_index=candidate.chunk_index,
                score=float(score),
                excerpt=candidate.excerpt,
            )
            for candidate, score in ranked[:top_k]
        ]


@lru_cache
def _load_cross_encoder(
    model_name: str,
) -> CrossEncoderLike:  # pragma: no cover - optional dependency path
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:  # pragma: no cover - exercised when optional dep missing
        raise RerankerUnavailableError(
            "sentence-transformers is not installed for cross-encoder reranking."
        ) from exc

    return CrossEncoder(model_name, trust_remote_code=False)

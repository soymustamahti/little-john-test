from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field

from src.core.config import OpenAIProviderSettings

RERANKING_SYSTEM_PROMPT = (
    "You rerank document chunks for retrieval. "
    "Return only chunk indexes that were provided. "
    "Prefer evidence that directly answers the query over background context. "
    "Scores must be between 0 and 1, where 1 means highly relevant."
)


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


class OpenAIRerankedItem(BaseModel):
    chunk_index: int = Field(ge=0)
    score: float = Field(ge=0, le=1)


class OpenAIRerankResponse(BaseModel):
    ranked_results: list[OpenAIRerankedItem]


class OpenAIDocumentReranker:
    provider_name = "openai"

    def __init__(
        self,
        settings: OpenAIProviderSettings,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or AsyncOpenAI(
            api_key=settings.api_key.get_secret_value(),
            timeout=settings.request_timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self._settings.reranking_model

    async def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[RerankCandidate],
        top_k: int,
    ) -> list[RerankedCandidate]:
        if not candidates:
            return []
        if not self._settings.is_configured:
            raise RerankerUnavailableError("OpenAI API settings are incomplete for reranking.")

        prompt = _build_reranking_prompt(query=query, candidates=candidates, top_k=top_k)

        try:
            response = await self._client.responses.parse(
                model=self._settings.reranking_model,
                input=[
                    {"role": "system", "content": RERANKING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                text_format=OpenAIRerankResponse,
                temperature=0,
                max_output_tokens=400,
            )
        except OpenAIError as exc:
            raise RerankerUnavailableError(
                f"OpenAI reranking is unavailable for '{self._settings.reranking_model}'."
            ) from exc

        parsed = response.output_parsed
        if parsed is None:
            raise RerankerUnavailableError("OpenAI reranking returned no structured output.")

        candidates_by_index = {candidate.chunk_index: candidate for candidate in candidates}
        reranked: list[RerankedCandidate] = []
        seen_chunk_indexes: set[int] = set()
        for item in parsed.ranked_results:
            candidate = candidates_by_index.get(item.chunk_index)
            if candidate is None or item.chunk_index in seen_chunk_indexes:
                continue
            seen_chunk_indexes.add(item.chunk_index)
            reranked.append(
                RerankedCandidate(
                    chunk_index=item.chunk_index,
                    score=float(item.score),
                    excerpt=candidate.excerpt,
                )
            )
            if len(reranked) >= top_k:
                break

        if not reranked:
            raise RerankerUnavailableError("OpenAI reranking returned no valid chunk indexes.")

        return reranked


def build_document_reranker(settings: OpenAIProviderSettings) -> DocumentReranker | None:
    if not settings.is_configured:
        return None

    normalized_model_name = settings.reranking_model.strip()
    if not normalized_model_name:
        return None

    return OpenAIDocumentReranker(settings)


def _build_reranking_prompt(
    *,
    query: str,
    candidates: Sequence[RerankCandidate],
    top_k: int,
) -> str:
    candidate_blocks = [
        (
            f"Chunk {candidate.chunk_index}:\n"
            f"{_normalize_candidate_text(candidate.content)}"
        )
        for candidate in candidates
    ]
    return (
        f"Query:\n{query.strip()}\n\n"
        f"Return up to {top_k} ranked chunks sorted from most relevant to least relevant.\n"
        "Use only the provided chunk_index values.\n\n"
        "Candidates:\n\n"
        + "\n\n".join(candidate_blocks)
    )


def _normalize_candidate_text(content: str, max_characters: int = 1_200) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_characters:
        return normalized
    return f"{normalized[: max_characters - 3].rstrip()}..."

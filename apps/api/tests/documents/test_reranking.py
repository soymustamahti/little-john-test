from typing import Any, cast

import pytest
from src.core.config import OpenAIProviderSettings
from src.documents.reranking import (
    OpenAIDocumentReranker,
    OpenAIRerankResponse,
    RerankCandidate,
    RerankerUnavailableError,
    build_document_reranker,
)


class FakeResponsesClient:
    def __init__(self, parsed_response: OpenAIRerankResponse | None) -> None:
        self._parsed_response = parsed_response
        self.calls: list[dict[str, object]] = []

    async def parse(self, **kwargs: object) -> Any:
        self.calls.append(kwargs)
        return type("ParsedResponse", (), {"output_parsed": self._parsed_response})()


class FakeOpenAIClient:
    def __init__(self, parsed_response: OpenAIRerankResponse | None) -> None:
        self.responses = FakeResponsesClient(parsed_response)


def test_build_document_reranker_returns_none_without_api_key() -> None:
    settings = OpenAIProviderSettings(api_key="", reranking_model="gpt-4o-mini")

    assert build_document_reranker(settings) is None


def test_build_document_reranker_returns_none_when_model_name_is_blank() -> None:
    settings = OpenAIProviderSettings(api_key="test-key", reranking_model="")

    assert build_document_reranker(settings) is None


@pytest.mark.asyncio
async def test_openai_document_reranker_returns_ranked_candidates() -> None:
    settings = OpenAIProviderSettings(api_key="test-key", reranking_model="gpt-4o-mini")
    client = FakeOpenAIClient(
        OpenAIRerankResponse.model_validate(
            {
                "ranked_results": [
                    {"chunk_index": 3, "score": 0.92},
                    {"chunk_index": 1, "score": 0.61},
                    {"chunk_index": 99, "score": 0.55},
                ]
            }
        )
    )
    reranker = OpenAIDocumentReranker(settings, client=cast(Any, client))

    results = await reranker.rerank(
        query="what is the insured address",
        candidates=[
            RerankCandidate(
                chunk_index=1,
                content="Policy summary",
                excerpt="Policy summary",
            ),
            RerankCandidate(
                chunk_index=3,
                content="Insured address",
                excerpt="Insured address",
            ),
        ],
        top_k=2,
    )

    assert [result.chunk_index for result in results] == [3, 1]
    assert client.responses.calls[0]["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_openai_document_reranker_raises_when_response_is_empty() -> None:
    settings = OpenAIProviderSettings(api_key="test-key", reranking_model="gpt-4o-mini")
    client = FakeOpenAIClient(None)
    reranker = OpenAIDocumentReranker(settings, client=cast(Any, client))

    with pytest.raises(RerankerUnavailableError):
        await reranker.rerank(
            query="query",
            candidates=[
                RerankCandidate(
                    chunk_index=1,
                    content="Chunk one",
                    excerpt="Chunk one",
                ),
            ],
            top_k=1,
        )

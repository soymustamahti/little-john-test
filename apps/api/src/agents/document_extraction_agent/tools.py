from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any
from uuid import UUID

from langgraph.config import get_stream_writer

from src.documents.retrieval import DocumentRetrievalService
from src.documents.runtime import get_document_retrieval_service


@lru_cache
def _get_retrieval_service() -> DocumentRetrievalService:
    return get_document_retrieval_service()


def _emit_progress(message: str) -> None:
    try:
        writer = get_stream_writer()
    except RuntimeError:
        return

    writer(
        {
            "phase": "planning_and_retrieving",
            "message": message,
        }
    )


def _summarize_query(query: str, max_characters: int = 72) -> str:
    normalized = " ".join(query.split())
    if len(normalized) <= max_characters:
        return normalized
    return f"{normalized[: max_characters - 3].rstrip()}..."


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural or f"{singular}s"


async def keyword_search(document_id: str, query: str, top_k: int = 5) -> dict[str, object]:
    """Search the document with lexical matching for exact terms, identifiers, and labels."""
    summarized_query = _summarize_query(query)
    _emit_progress(
        f"Running keyword search for '{summarized_query}' across the document chunks."
    )
    results = await _get_retrieval_service().keyword_search(
        document_id=UUID(document_id),
        query=query,
        top_k=max(1, min(top_k, 8)),
    )
    _emit_progress(
        f"Keyword search found {len(results)} {_pluralize(len(results), 'candidate chunk')} "
        f"for '{summarized_query}'."
    )
    return {
        "query": query,
        "results": [
            {
                "chunk_index": result.chunk_index,
                "score": round(result.score, 4),
                "match_type": result.match_type,
                "excerpt": result.excerpt,
            }
            for result in results
        ],
    }


async def semantic_search(document_id: str, query: str, top_k: int = 5) -> dict[str, object]:
    """Search the document with embedding similarity for paraphrased or descriptive queries."""
    summarized_query = _summarize_query(query)
    _emit_progress(
        f"Running semantic retrieval for '{summarized_query}' with document embeddings."
    )
    results = await _get_retrieval_service().semantic_search(
        document_id=UUID(document_id),
        query=query,
        top_k=max(1, min(top_k, 8)),
    )
    _emit_progress(
        f"Semantic retrieval found {len(results)} {_pluralize(len(results), 'candidate chunk')} "
        f"for '{summarized_query}'."
    )
    return {
        "query": query,
        "results": [
            {
                "chunk_index": result.chunk_index,
                "score": round(result.score, 4),
                "match_type": result.match_type,
                "excerpt": result.excerpt,
            }
            for result in results
        ],
    }


async def hybrid_search(document_id: str, query: str, top_k: int = 5) -> dict[str, object]:
    """Run keyword and semantic retrieval, then return the merged evidence set."""
    summarized_query = _summarize_query(query)
    _emit_progress(
        "Running hybrid retrieval for "
        f"'{summarized_query}' with keyword, semantic, and reranking stages."
    )
    results = await _get_retrieval_service().hybrid_search(
        document_id=UUID(document_id),
        query=query,
        top_k=max(1, min(top_k, 8)),
    )
    _emit_progress(
        f"Hybrid retrieval returned {len(results)} {_pluralize(len(results), 'ranked chunk')} "
        f"for '{summarized_query}'."
    )
    return {
        "query": query,
        "results": [
            {
                "chunk_index": result.chunk_index,
                "score": round(result.score, 4),
                "match_type": result.match_type,
                "excerpt": result.excerpt,
            }
            for result in results
        ],
    }


async def inspect_chunk(document_id: str, chunk_index: int) -> dict[str, object]:
    """Read a specific document chunk in full when a search result looks promising."""
    _emit_progress(f"Inspecting chunk {chunk_index} in full to verify the evidence.")
    result = await _get_retrieval_service().inspect_chunk(
        document_id=UUID(document_id),
        chunk_index=chunk_index,
    )
    _emit_progress(
        f"Chunk {chunk_index} inspection is ready for the next extraction decision."
    )
    return {
        "chunk_index": result.chunk_index,
        "match_type": result.match_type,
        "excerpt": result.excerpt,
    }


async def inspect_spreadsheet(
    document_id: str,
    sheet_name: str | None = None,
    max_rows: int = 20,
) -> dict[str, object]:
    """Inspect a spreadsheet sheet preview with pandas when tabular structure matters."""
    selected_sheet = sheet_name.strip() if sheet_name else "the first sheet"
    _emit_progress(
        f"Opening {selected_sheet} with pandas to inspect the tabular structure."
    )
    result = await _get_retrieval_service().inspect_spreadsheet(
        document_id=UUID(document_id),
        sheet_name=sheet_name,
        max_rows=max(1, min(max_rows, 50)),
    )
    rows = result.get("rows")
    columns = result.get("columns")
    row_count = len(rows) if isinstance(rows, list) else 0
    column_count = len(columns) if isinstance(columns, list) else 0
    _emit_progress(
        f"Loaded spreadsheet preview with {row_count} {_pluralize(row_count, 'row')} "
        f"and {column_count} {_pluralize(column_count, 'column')}."
    )
    return result


TOOLS: list[Callable[..., Any]] = [
    hybrid_search,
    keyword_search,
    semantic_search,
    inspect_chunk,
    inspect_spreadsheet,
]

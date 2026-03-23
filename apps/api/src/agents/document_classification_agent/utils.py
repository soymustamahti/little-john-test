from collections.abc import Sequence

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.documents.classification_service import ClassificationSourceChunk


def load_classification_model(model_name: str) -> BaseChatModel:
    return init_chat_model(model_name, model_provider="openai")


def build_classification_excerpt(
    *,
    extracted_text: str,
    chunks: Sequence[ClassificationSourceChunk],
    max_characters: int,
    max_chunks: int = 8,
) -> tuple[str, list[int]]:
    if max_characters <= 0:
        return "", []

    if chunks:
        selected_positions = _select_chunk_positions(len(chunks), max_chunks)
        excerpt_parts: list[str] = []
        sampled_chunk_indices: list[int] = []
        used_characters = 0

        for position in selected_positions:
            chunk = chunks[position]
            chunk_text = chunk.content.strip()
            if not chunk_text:
                continue

            remaining_characters = max_characters - used_characters
            if remaining_characters <= 0:
                break

            excerpt_snippet = chunk_text[:remaining_characters].strip()
            if not excerpt_snippet:
                continue

            excerpt_parts.append(f"[chunk {chunk.chunk_index}]\n{excerpt_snippet}")
            sampled_chunk_indices.append(chunk.chunk_index)
            used_characters += len(excerpt_snippet)

        excerpt_text = "\n\n".join(excerpt_parts).strip()
        if excerpt_text:
            return excerpt_text, sampled_chunk_indices

    fallback_excerpt = extracted_text.strip()[:max_characters].strip()
    return fallback_excerpt, []


def _select_chunk_positions(total_chunks: int, max_chunks: int) -> list[int]:
    if total_chunks <= 0:
        return []
    if max_chunks <= 1:
        return [0]
    if total_chunks <= max_chunks:
        return list(range(total_chunks))

    step = (total_chunks - 1) / (max_chunks - 1)
    selected_positions = {round(step * index) for index in range(max_chunks)}
    return sorted(selected_positions)

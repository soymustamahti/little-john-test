from chonkie import RecursiveChunker


class DocumentTextChunker:
    def __init__(self, *, chunk_size: int, min_characters_per_chunk: int) -> None:
        self._chunker = RecursiveChunker(
            chunk_size=chunk_size,
            min_characters_per_chunk=min_characters_per_chunk,
        )

    def chunk_text(self, text: str) -> list[tuple[str, int, int]]:
        normalized_text = text.strip()
        if not normalized_text:
            return []

        chunks = self._chunker(normalized_text)
        return [(chunk.text, chunk.start_index, chunk.end_index) for chunk in chunks]

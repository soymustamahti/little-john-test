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

        raw_chunks = self._chunker(normalized_text)
        if isinstance(raw_chunks, list):
            chunk_items: list[object] = list(raw_chunks)
        else:
            chunk_items = [raw_chunks]

        return [
            (
                str(getattr(chunk, "text")),
                int(getattr(chunk, "start_index")),
                int(getattr(chunk, "end_index")),
            )
            for chunk in chunk_items
        ]

from dataclasses import dataclass, field


@dataclass
class InputState:
    document_id: str
    thread_id: str


@dataclass
class State(InputState):
    original_filename: str = ""
    excerpt_text: str = ""
    sampled_chunk_indices: list[int] = field(default_factory=list)
    excerpt_character_count: int = 0
    categories: list[dict[str, str]] = field(default_factory=list)
    decision: str | None = None
    matched_category_id: str | None = None
    suggested_category_name: str | None = None
    suggested_category_label_key: str | None = None
    confidence: float | None = None
    rationale: str | None = None
    review_action: str | None = None

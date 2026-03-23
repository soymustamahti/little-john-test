from __future__ import annotations

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class DocumentClassificationDecision(BaseModel):
    decision: Literal["match_existing_category", "suggest_new_category"]
    matched_category_id: UUID | None = None
    suggested_category_name: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=120),
    ]
    suggested_category_label_key: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=120),
    ]
    confidence: Annotated[float, Field(ge=0, le=1)]
    rationale: Annotated[str, Field(min_length=1, max_length=1200)]

    @model_validator(mode="after")
    def validate_decision_fields(self) -> Self:
        if self.decision == "match_existing_category" and self.matched_category_id is None:
            raise ValueError("matched_category_id is required when matching an existing category.")
        if self.decision == "suggest_new_category" and (
            self.suggested_category_name is None or self.suggested_category_label_key is None
        ):
            raise ValueError(
                "suggested_category_name and suggested_category_label_key are required "
                "when suggesting a new category."
            )
        return self

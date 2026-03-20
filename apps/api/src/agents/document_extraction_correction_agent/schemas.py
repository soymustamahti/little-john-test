from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from src.agents.document_extraction_agent.schemas import ExtractionResultDraft


class CorrectionFinalizerDraft(BaseModel):
    assistant_response: Annotated[str, Field(min_length=1, max_length=1200)]
    reasoning_summary: Annotated[str, Field(min_length=1, max_length=1200)]
    updates: ExtractionResultDraft = Field(default_factory=ExtractionResultDraft)

    @field_validator("assistant_response", mode="before")
    @classmethod
    def _normalize_assistant_response(cls, value: object) -> str:
        return _normalize_text(
            value,
            fallback="I reviewed your request and updated the extraction draft when needed.",
        )

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def _normalize_reasoning_summary(cls, value: object) -> str:
        return _normalize_text(value, fallback="Correction review ready.")

    @field_validator("updates", mode="before")
    @classmethod
    def _normalize_updates(
        cls,
        value: object,
    ) -> dict[str, object]:
        if value is None:
            return {"modules": []}

        if isinstance(value, list):
            return {"modules": [item for item in value if isinstance(item, dict)]}

        if not isinstance(value, dict):
            return {"modules": []}

        raw_modules = value.get("modules")
        if isinstance(raw_modules, list):
            return {"modules": [item for item in raw_modules if isinstance(item, dict)]}

        if isinstance(raw_modules, dict):
            normalized_modules: list[dict[str, object]] = []
            for module_key, module_value in raw_modules.items():
                normalized_module = _normalize_named_module(module_key, module_value)
                if normalized_module is not None:
                    normalized_modules.append(normalized_module)
            return {"modules": normalized_modules}

        module_key = value.get("key")
        raw_fields = value.get("fields")
        if isinstance(module_key, str) and isinstance(raw_fields, list):
            return {"modules": [value]}

        named_modules: list[dict[str, object]] = []
        for named_module_key, named_module_value in value.items():
            normalized_module = _normalize_named_module(
                named_module_key,
                named_module_value,
            )
            if normalized_module is not None:
                named_modules.append(normalized_module)
        return {"modules": named_modules}


def _normalize_text(value: object, *, fallback: str) -> str:
    if isinstance(value, str):
        normalized = " ".join(value.split()).strip()
    else:
        normalized = ""

    return normalized[:1200] if normalized else fallback


def _normalize_named_module(
    module_key: object,
    module_value: object,
) -> dict[str, object] | None:
    if not isinstance(module_key, str):
        return None

    normalized_key = module_key.strip()
    if normalized_key == "":
        return None

    if isinstance(module_value, dict):
        normalized_module = dict(module_value)
    elif isinstance(module_value, list):
        normalized_module = {"fields": module_value}
    else:
        return None

    normalized_module.setdefault("key", normalized_key)
    return normalized_module

from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.documents.extraction import ExtractionValueMode
from src.documents.extraction_schemas import DocumentExtractionResultRead
from src.extraction_templates.schemas import (
    ScalarTemplateField,
    ScalarValueType,
    TableColumnDefinition,
    TableTemplateField,
    TemplateModule,
)

MAX_REASONING_SUMMARY_LENGTH = 1200


def normalize_reasoning_summary(value: object) -> str:
    if isinstance(value, str):
        normalized = " ".join(value.split()).strip()
    else:
        normalized = ""

    if not normalized:
        normalized = "Structured extraction ready."

    if len(normalized) <= MAX_REASONING_SUMMARY_LENGTH:
        return normalized

    return normalized[: MAX_REASONING_SUMMARY_LENGTH - 3].rstrip() + "..."


def normalize_extraction_result(
    *,
    template_modules: list[dict[str, object]],
    raw_result: object,
) -> DocumentExtractionResultRead:
    validated_template_modules = [
        TemplateModule.model_validate(module) for module in template_modules
    ]
    raw_modules = _extract_collection(
        raw_result.get("modules") if isinstance(raw_result, dict) else raw_result
    )
    raw_modules_index = _index_items(raw_modules)

    normalized_modules = [
        _normalize_module(
            template_module=template_module,
            raw_module=_lookup_item(
                raw_modules_index,
                key=template_module.key,
                label=template_module.label,
            ),
        )
        for template_module in validated_template_modules
    ]

    return DocumentExtractionResultRead.model_validate({"modules": normalized_modules})


def extraction_result_has_values(result: DocumentExtractionResultRead) -> bool:
    for module in result.modules:
        for field in module.fields:
            if field.kind == "scalar":
                if _has_meaningful_scalar_value(field.value):
                    return True
                continue

            if field.rows:
                return True

    return False


def _normalize_module(
    *,
    template_module: TemplateModule,
    raw_module: dict[str, Any] | None,
) -> dict[str, Any]:
    raw_fields_index = _index_items(
        _extract_collection(
            raw_module.get("fields") if isinstance(raw_module, dict) else raw_module
        )
    )
    normalized_fields: list[dict[str, Any]] = []

    for template_field in template_module.fields:
        raw_field = _lookup_item(
            raw_fields_index,
            key=template_field.key,
            label=template_field.label,
        )
        if isinstance(template_field, ScalarTemplateField):
            normalized_fields.append(
                _normalize_scalar_field(
                    template_field=template_field,
                    raw_field=raw_field,
                )
            )
            continue

        if isinstance(template_field, TableTemplateField):
            normalized_fields.append(
                _normalize_table_field(
                    template_field=template_field,
                    raw_field=raw_field,
                )
            )

    return {
        "key": template_module.key,
        "label": template_module.label,
        "fields": normalized_fields,
    }


def _normalize_scalar_field(
    *,
    template_field: ScalarTemplateField,
    raw_field: dict[str, Any] | None,
) -> dict[str, Any]:
    value = _normalize_scalar_value(
        raw_field.get("value") if raw_field else None,
        template_field.value_type,
    )
    raw_value = _normalize_raw_value(raw_field.get("raw_value") if raw_field else None, value)

    return {
        "kind": "scalar",
        "key": template_field.key,
        "label": template_field.label,
        "value_type": template_field.value_type,
        "required": template_field.required,
        "value": value,
        "raw_value": raw_value,
        "confidence": _normalize_confidence(raw_field.get("confidence") if raw_field else None),
        "extraction_mode": _normalize_extraction_mode(
            raw_field.get("extraction_mode") if raw_field else None,
            value,
        ),
        "evidence": _normalize_evidence(raw_field.get("evidence") if raw_field else None),
    }


def _normalize_table_field(
    *,
    template_field: TableTemplateField,
    raw_field: dict[str, Any] | None,
) -> dict[str, Any]:
    raw_rows = _extract_collection(
        raw_field.get("rows") if isinstance(raw_field, dict) else raw_field,
        identifier_key="row_index",
    )
    normalized_rows = [
        _normalize_table_row(
            raw_row=raw_row,
            template_field=template_field,
            fallback_row_index=index,
        )
        for index, raw_row in enumerate(raw_rows)
    ]

    return {
        "kind": "table",
        "key": template_field.key,
        "label": template_field.label,
        "required": template_field.required,
        "min_rows": template_field.min_rows,
        "rows": normalized_rows,
    }


def _normalize_table_row(
    *,
    raw_row: dict[str, Any],
    template_field: TableTemplateField,
    fallback_row_index: int,
) -> dict[str, Any]:
    raw_cells_index = _index_items(
        _extract_collection(
            raw_row.get("cells") if isinstance(raw_row, dict) else raw_row
        )
    )

    return {
        "row_index": _normalize_row_index(raw_row.get("row_index"), fallback_row_index),
        "confidence": _normalize_confidence(raw_row.get("confidence")),
        "cells": [
            _normalize_table_cell(
                template_column=template_column,
                raw_cell=_lookup_item(
                    raw_cells_index,
                    key=template_column.key,
                    label=template_column.label,
                ),
            )
            for template_column in template_field.columns
        ],
    }


def _normalize_table_cell(
    *,
    template_column: TableColumnDefinition,
    raw_cell: dict[str, Any] | None,
) -> dict[str, Any]:
    value = _normalize_scalar_value(
        raw_cell.get("value") if raw_cell else None,
        template_column.value_type,
    )
    raw_value = _normalize_raw_value(raw_cell.get("raw_value") if raw_cell else None, value)

    return {
        "key": template_column.key,
        "label": template_column.label,
        "value_type": template_column.value_type,
        "required": template_column.required,
        "value": value,
        "raw_value": raw_value,
        "confidence": _normalize_confidence(raw_cell.get("confidence") if raw_cell else None),
        "extraction_mode": _normalize_extraction_mode(
            raw_cell.get("extraction_mode") if raw_cell else None,
            value,
        ),
        "evidence": _normalize_evidence(raw_cell.get("evidence") if raw_cell else None),
    }


def _extract_collection(
    items: object,
    *,
    identifier_key: str = "key",
) -> list[dict[str, Any]]:
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]

    if not isinstance(items, dict):
        return []

    normalized_items: list[dict[str, Any]] = []
    for item_key, item_value in items.items():
        if isinstance(item_value, dict):
            normalized_item = dict(item_value)
        else:
            normalized_item = {"value": item_value}

        if identifier_key == "row_index":
            normalized_item.setdefault("row_index", item_key)
        else:
            normalized_item.setdefault("key", str(item_key))

        normalized_items.append(normalized_item)

    return normalized_items


def _index_items(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        for raw_candidate in (
            item.get("key"),
            item.get("label"),
            item.get("name"),
            item.get("title"),
        ):
            token = _normalize_lookup_token(raw_candidate)
            if token:
                indexed[token] = item
    return indexed


def _lookup_item(
    indexed_items: dict[str, dict[str, Any]],
    *,
    key: str,
    label: str,
) -> dict[str, Any] | None:
    return indexed_items.get(_normalize_lookup_token(key)) or indexed_items.get(
        _normalize_lookup_token(label)
    )


def _normalize_lookup_token(value: object) -> str:
    if not isinstance(value, str):
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    collapsed = re.sub(r"[^a-z0-9]+", "", ascii_only.lower())
    return collapsed


def _normalize_scalar_value(
    value: object,
    value_type: ScalarValueType,
) -> str | float | bool | None:
    if value is None:
        return None

    if value_type == ScalarValueType.BOOLEAN:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "oui", "1"}:
                return True
            if normalized in {"false", "no", "non", "0"}:
                return False
        return None

    if value_type == ScalarValueType.NUMBER:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            try:
                return float(normalized.replace(" ", "").replace(",", "."))
            except ValueError:
                return normalized
        return None

    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None

    if isinstance(value, bool | int | float):
        return str(value)

    return None


def _has_meaningful_scalar_value(value: str | float | bool | None) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def _normalize_raw_value(
    raw_value: object,
    normalized_value: str | float | bool | None,
) -> str | None:
    if isinstance(raw_value, str):
        normalized = raw_value.strip()
        if normalized:
            return normalized

    if normalized_value is None:
        return None

    if isinstance(normalized_value, str):
        return normalized_value

    return str(normalized_value)


def _normalize_confidence(value: object) -> float:
    if isinstance(value, bool):
        return 0

    if isinstance(value, int | float):
        numeric_value = float(value)
    elif isinstance(value, str):
        try:
            numeric_value = float(value.strip().replace("%", ""))
        except ValueError:
            return 0
    else:
        return 0

    if numeric_value > 1 and numeric_value <= 100:
        numeric_value = numeric_value / 100

    return max(0, min(numeric_value, 1))


def _normalize_extraction_mode(
    value: object,
    normalized_value: str | float | bool | None,
) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {
            ExtractionValueMode.DIRECT.value,
            ExtractionValueMode.INFERRED.value,
            ExtractionValueMode.NOT_FOUND.value,
        }:
            return normalized

    if normalized_value is None:
        return ExtractionValueMode.NOT_FOUND.value

    return ExtractionValueMode.DIRECT.value


def _normalize_evidence(value: object) -> dict[str, Any] | None:
    evidence_items: list[dict[str, Any]] = []
    if isinstance(value, dict):
        evidence_items = [value]
    elif isinstance(value, list):
        evidence_items = [item for item in value if isinstance(item, dict)]
    elif isinstance(value, str):
        stripped = value.strip()
        return {"source_chunk_indices": [], "source_excerpt": stripped or None}

    if not evidence_items:
        return None

    chunk_indices: list[int] = []
    source_excerpt: str | None = None
    for item in evidence_items:
        raw_indices = item.get("source_chunk_indices")
        if isinstance(raw_indices, list):
            for raw_index in raw_indices:
                if isinstance(raw_index, int) and raw_index not in chunk_indices:
                    chunk_indices.append(raw_index)
        if source_excerpt is None:
            raw_excerpt = item.get("source_excerpt")
            if isinstance(raw_excerpt, str):
                normalized_excerpt = raw_excerpt.strip()
                if normalized_excerpt:
                    source_excerpt = normalized_excerpt

    if not chunk_indices and source_excerpt is None:
        return None

    return {
        "source_chunk_indices": chunk_indices,
        "source_excerpt": source_excerpt,
    }


def _normalize_row_index(value: object, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, str):
        try:
            return max(0, int(value.strip()))
        except ValueError:
            return fallback
    return fallback

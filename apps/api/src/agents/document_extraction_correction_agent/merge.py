from __future__ import annotations

from src.agents.document_extraction_agent.normalization import normalize_extraction_result
from src.documents.extraction_schemas import DocumentExtractionResultRead


def apply_extraction_corrections(
    *,
    template_modules: list[dict[str, object]],
    current_result: DocumentExtractionResultRead,
    raw_updates: dict[str, object],
) -> DocumentExtractionResultRead:
    update_targets = _collect_update_targets(raw_updates)
    if not update_targets:
        return current_result

    normalized_patch = normalize_extraction_result(
        template_modules=template_modules,
        raw_result=raw_updates,
    )
    next_result = current_result.model_copy(deep=True)

    for module_index, module in enumerate(next_result.modules):
        patch_module = next(
            (candidate for candidate in normalized_patch.modules if candidate.key == module.key),
            None,
        )
        if patch_module is None:
            continue

        for field_index, field in enumerate(module.fields):
            if (module.key, field.key) not in update_targets:
                continue

            patch_field = next(
                (candidate for candidate in patch_module.fields if candidate.key == field.key),
                None,
            )
            if patch_field is None:
                continue

            next_result.modules[module_index].fields[field_index] = patch_field

    return next_result


def _collect_update_targets(raw_updates: object) -> set[tuple[str, str]]:
    if not isinstance(raw_updates, dict):
        return set()

    raw_modules = raw_updates.get("modules")
    if not isinstance(raw_modules, list):
        return set()

    targets: set[tuple[str, str]] = set()
    for raw_module in raw_modules:
        if not isinstance(raw_module, dict):
            continue

        module_key = raw_module.get("key")
        raw_fields = raw_module.get("fields")
        if not isinstance(module_key, str) or not isinstance(raw_fields, list):
            continue

        normalized_module_key = module_key.strip()
        if normalized_module_key == "":
            continue

        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue

            field_key = raw_field.get("key")
            if not isinstance(field_key, str):
                continue

            normalized_field_key = field_key.strip()
            if normalized_field_key == "":
                continue

            targets.add((normalized_module_key, normalized_field_key))

    return targets

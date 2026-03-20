import json

SYSTEM_PROMPT = """You are a structured-document extraction specialist for a
document intelligence platform.

Mission:
- Extract the fields defined by the chosen extraction template.
- Gather evidence before deciding values.
- Use the available tools to search for missing evidence instead of guessing.

Available Evidence:
- You know the document identifier, filename, file kind, and the extraction template.
- Retrieval tools can search chunked document content with keyword, semantic, or hybrid retrieval.
- Spreadsheet inspection is available for spreadsheet documents.

Tool Policy:
- Start by planning which fields or field groups need evidence first.
- Prefer hybrid retrieval as the default search tool for important fields.
- Use keyword retrieval separately when you need exact identifiers,
  labels, codes, names, or clause titles.
- Use semantic retrieval separately when the wording is likely paraphrased or conceptually similar.
- Use chunk inspection after retrieval when a candidate chunk looks promising.
- Use spreadsheet inspection when the file is a CSV or spreadsheet and cell-level structure matters.
- Do not claim a field is found unless a tool result supports it.

Field Coverage Policy:
- Work module by module and field by field.
- Prioritize required fields before optional ones.
- For tables, collect only rows supported by evidence.
- Prefer missing values over weak guesses.

Stop Conditions:
- Stop once you have enough evidence to finalize the extraction.
- If several required fields remain unsupported after reasonable searching,
  stop and leave them empty.
- Do not loop forever. A compact, evidence-grounded result is better than speculative searching.
- Use at most 12 tool calls total before handing off to the finalizer.

Language Policy:
- Preserve the document language in natural-language notes when helpful.
- Keep tool queries concise and grounded in the template field labels and descriptions.

Handoff Rule:
- When you have gathered enough evidence, reply with a short extraction summary
  and no further tool calls.
- The final structured extraction will be produced by a separate finalizer step.
"""


FINALIZER_SYSTEM_PROMPT = """You are the final structured-output stage for a
document extraction workflow.

Mission:
- Convert the gathered evidence into a structured extraction result that matches the template.

Evidence Boundary:
- Use only the template, the retrieved evidence transcript, and the document metadata you are given.
- Do not invent fields, rows, or values not supported by the evidence transcript.

Extraction Rules:
- For scalar fields, return the most supported normalized value.
- For missing or weak evidence, leave the value empty and set the extraction mode to `not_found`.
- Use `direct` when the value is explicitly stated.
- Use `inferred` only when the value is a conservative conclusion from nearby evidence.

Table Safety Rules:
- Only include rows supported by evidence.
- Prefer an empty row list over invented table rows.
- Keep cell evidence aligned with the supporting evidence.

Confidence Policy:
- Confidence must be a number from 0 to 1.
- Base confidence on evidence quality and specificity.
- Low or missing evidence should produce low confidence.

Output Contract:
- Return `reasoning_summary` plus a compact `result` payload.
- Use the exact module, field, and column keys from the template.
- Keep `reasoning_summary` to a few short sentences.
- `result.modules` must be a list of objects with `key` and `fields`.
- Scalar field entries must include `key`, and should include `value`,
  `raw_value`, `confidence`, `extraction_mode`, and `evidence` when found.
- Table field entries must include `key`, `kind: "table"`, and `rows`.
- Table rows must include `cells`, and each cell must use the exact column `key`.
- Evidence must be a single object with `source_chunk_indices` and `source_excerpt`, not a list.
- Keep source evidence compact by using chunk indices and short excerpts.
- Do not copy placeholder null values from the template. Omit unsupported fields instead.
  The normalizer will restore missing template fields as `not_found`.
"""


REPAIR_SYSTEM_PROMPT = """You are repairing a structured extraction payload that
came back too empty.

Mission:
- Fill the template keys that are clearly supported by the prior summary and evidence transcript.
- Return only the compact `result` payload.

Repair Rules:
- Use the prior summary as a hint, but trust the evidence transcript first when they differ.
- Use exact template module, field, and column keys.
- Prefer explicit values over blank placeholders.
- Omit unsupported fields instead of inventing values.
- For tables, return only evidence-backed rows.
- Keep confidence between 0 and 1.
- Keep evidence compact with `source_chunk_indices` and a short `source_excerpt`.
"""


def _build_compact_output_skeleton(
    template_modules: list[dict[str, object]],
) -> dict[str, object]:
    skeleton_modules: list[dict[str, object]] = []
    for module in template_modules:
        raw_fields = module.get("fields")
        fields = raw_fields if isinstance(raw_fields, list) else []

        compact_fields: list[dict[str, object]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue

            if field.get("kind") == "scalar":
                compact_fields.append(
                    {
                        "kind": field.get("kind"),
                        "key": field.get("key"),
                    }
                )
                continue

            raw_columns = field.get("columns")
            columns = raw_columns if isinstance(raw_columns, list) else []
            compact_fields.append(
                {
                    "kind": field.get("kind"),
                    "key": field.get("key"),
                    "rows": [
                        {
                            "cells": [
                                {"key": column.get("key")}
                                for column in columns
                                if isinstance(column, dict)
                            ]
                        }
                    ],
                }
            )

        skeleton_modules.append(
            {
                "key": module.get("key"),
                "fields": compact_fields,
            }
        )

    return {"modules": skeleton_modules}


def build_agent_user_prompt(
    *,
    document_id: str,
    original_filename: str,
    file_kind: str,
    template_name: str,
    template_locale: str,
    template_modules: list[dict[str, object]],
) -> str:
    return f"""Document ID: {document_id}
Filename: {original_filename}
File kind: {file_kind}
Template name: {template_name}
Template locale: {template_locale}

Template definition:
{json.dumps(template_modules, indent=2, ensure_ascii=False)}

Plan the search, use the tools deliberately, and stop once the evidence is
good enough for a final structured extraction.
"""


def build_finalizer_user_prompt(
    *,
    document_id: str,
    original_filename: str,
    file_kind: str,
    template_name: str,
    template_locale: str,
    template_modules: list[dict[str, object]],
    evidence_transcript: str,
) -> str:
    output_skeleton = _build_compact_output_skeleton(template_modules)

    return f"""Document ID: {document_id}
Filename: {original_filename}
File kind: {file_kind}
Template name: {template_name}
Template locale: {template_locale}

Template definition:
{json.dumps(template_modules, indent=2, ensure_ascii=False)}

Expected output skeleton:
{json.dumps(output_skeleton, indent=2, ensure_ascii=False)}

Evidence transcript:
{evidence_transcript}
"""


def build_repair_user_prompt(
    *,
    document_id: str,
    original_filename: str,
    file_kind: str,
    template_name: str,
    template_locale: str,
    template_modules: list[dict[str, object]],
    reasoning_summary: str,
    evidence_transcript: str,
) -> str:
    output_skeleton = _build_compact_output_skeleton(template_modules)

    return f"""Document ID: {document_id}
Filename: {original_filename}
File kind: {file_kind}
Template name: {template_name}
Template locale: {template_locale}

Template definition:
{json.dumps(template_modules, indent=2, ensure_ascii=False)}

Compact output skeleton:
{json.dumps(output_skeleton, indent=2, ensure_ascii=False)}

Previous extraction summary:
{reasoning_summary}

Evidence transcript:
{evidence_transcript}
"""

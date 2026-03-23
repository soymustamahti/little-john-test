from src.agents.document_extraction_agent.normalization import (
    MAX_REASONING_SUMMARY_LENGTH,
    extraction_result_has_values,
    normalize_extraction_result,
    normalize_reasoning_summary,
)


def test_normalize_extraction_result_rehydrates_template_kinds_and_evidence() -> None:
    normalized = normalize_extraction_result(
        template_modules=[
            {
                "key": "parties",
                "label": "Parties",
                "fields": [
                    {
                        "kind": "scalar",
                        "key": "client_name",
                        "label": "Client Name",
                        "required": True,
                        "value_type": "string",
                    },
                    {
                        "kind": "table",
                        "key": "deliverables",
                        "label": "Deliverables",
                        "required": False,
                        "min_rows": 0,
                        "columns": [
                            {
                                "key": "name",
                                "label": "Name",
                                "value_type": "string",
                                "required": True,
                            },
                            {
                                "key": "amount",
                                "label": "Amount",
                                "value_type": "number",
                                "required": False,
                            },
                        ],
                    },
                ],
            }
        ],
        raw_result={
            "modules": [
                {
                    "key": "parties",
                    "fields": [
                        {
                            "key": "client_name",
                            "value": "Ville de Bordeaux",
                            "confidence": 82,
                            "extraction_mode": "direct",
                            "evidence": [
                                {
                                    "source_chunk_indices": [4],
                                    "source_excerpt": (
                                        "Le maître d’ouvrage est la Ville de Bordeaux."
                                    ),
                                }
                            ],
                        },
                        {
                            "key": "deliverables",
                            "rows": [
                                {
                                    "cells": [
                                        {
                                            "key": "name",
                                            "value": "Audit initial",
                                            "evidence": "Audit initial",
                                        },
                                        {
                                            "key": "amount",
                                            "value": "325 360",
                                        },
                                    ]
                                }
                            ],
                        },
                    ],
                }
            ]
        },
    )

    scalar_field = normalized.modules[0].fields[0]
    assert scalar_field.kind == "scalar"
    assert scalar_field.confidence == 0.82
    assert scalar_field.evidence is not None
    assert scalar_field.evidence.source_chunk_indices == [4]

    table_field = normalized.modules[0].fields[1]
    assert table_field.kind == "table"
    assert len(table_field.rows) == 1
    assert table_field.rows[0].cells[1].value == 325360.0


def test_normalize_reasoning_summary_trims_and_defaults() -> None:
    long_summary = "resume " * 400

    normalized = normalize_reasoning_summary(long_summary)

    assert len(normalized) <= MAX_REASONING_SUMMARY_LENGTH
    assert normalized.endswith("...")
    assert normalize_reasoning_summary("   ") == "Structured extraction ready."


def test_normalize_extraction_result_supports_mapping_shapes_and_label_matching() -> None:
    normalized = normalize_extraction_result(
        template_modules=[
            {
                "key": "parties",
                "label": "Parties",
                "fields": [
                    {
                        "kind": "scalar",
                        "key": "maitre_ouvrage_nom",
                        "label": "Nom du maitre d'ouvrage",
                        "required": True,
                        "value_type": "string",
                    },
                    {
                        "kind": "table",
                        "key": "liste_annexes",
                        "label": "Liste des annexes",
                        "required": False,
                        "min_rows": 0,
                        "columns": [
                            {
                                "key": "reference_annexe",
                                "label": "Reference annexe",
                                "value_type": "string",
                                "required": True,
                            },
                            {
                                "key": "intitule_annexe",
                                "label": "Intitule annexe",
                                "value_type": "string",
                                "required": True,
                            },
                        ],
                    },
                ],
            }
        ],
        raw_result={
            "modules": {
                "Parties": {
                    "fields": {
                        "Nom du maitre d'ouvrage": {
                            "value": "Université Bordeaux Montaigne",
                            "confidence": "87",
                            "evidence": {
                                "source_chunk_indices": [0],
                                "source_excerpt": "Université Bordeaux Montaigne",
                            },
                        },
                        "Liste des annexes": {
                            "rows": {
                                "0": {
                                    "cells": {
                                        "Reference annexe": "Annexe n° 1",
                                        "Intitule annexe": "Programme",
                                    }
                                }
                            }
                        },
                    }
                }
            }
        },
    )

    scalar_field = normalized.modules[0].fields[0]
    assert scalar_field.value == "Université Bordeaux Montaigne"
    assert scalar_field.confidence == 0.87

    table_field = normalized.modules[0].fields[1]
    assert table_field.rows[0].cells[0].value == "Annexe n° 1"
    assert table_field.rows[0].cells[1].value == "Programme"


def test_extraction_result_has_values_detects_scalar_and_table_content() -> None:
    populated_scalar = normalize_extraction_result(
        template_modules=[
            {
                "key": "parties",
                "label": "Parties",
                "fields": [
                    {
                        "kind": "scalar",
                        "key": "maitre_ouvrage_nom",
                        "label": "Nom du maitre d'ouvrage",
                        "required": True,
                        "value_type": "string",
                    }
                ],
            }
        ],
        raw_result={
            "modules": [
                {
                    "key": "parties",
                    "fields": [
                        {
                            "key": "maitre_ouvrage_nom",
                            "value": "Université Bordeaux Montaigne",
                        }
                    ],
                }
            ]
        },
    )
    assert extraction_result_has_values(populated_scalar) is True

    populated_table = normalize_extraction_result(
        template_modules=[
            {
                "key": "annexes",
                "label": "Annexes",
                "fields": [
                    {
                        "kind": "table",
                        "key": "liste_annexes",
                        "label": "Liste des annexes",
                        "required": False,
                        "min_rows": 0,
                        "columns": [
                            {
                                "key": "reference_annexe",
                                "label": "Reference annexe",
                                "value_type": "string",
                                "required": True,
                            }
                        ],
                    }
                ],
            }
        ],
        raw_result={
            "modules": [
                {
                    "key": "annexes",
                    "fields": [
                        {
                            "key": "liste_annexes",
                            "rows": [{"cells": [{"key": "reference_annexe", "value": "Annexe 1"}]}],
                        }
                    ],
                }
            ]
        },
    )
    assert extraction_result_has_values(populated_table) is True

    empty_result = normalize_extraction_result(
        template_modules=[
            {
                "key": "identification",
                "label": "Identification",
                "fields": [
                    {
                        "kind": "scalar",
                        "key": "titre",
                        "label": "Titre",
                        "required": True,
                        "value_type": "string",
                    }
                ],
            }
        ],
        raw_result={"modules": [{"key": "identification", "fields": []}]},
    )
    assert extraction_result_has_values(empty_result) is False

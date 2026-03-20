from src.agents.document_extraction_agent.normalization import normalize_extraction_result
from src.agents.document_extraction_correction_agent.merge import (
    apply_extraction_corrections,
)
from src.agents.document_extraction_correction_agent.schemas import (
    CorrectionFinalizerDraft,
)


def test_apply_extraction_corrections_replaces_only_targeted_fields() -> None:
    template_modules = [
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
                    "kind": "scalar",
                    "key": "client_address",
                    "label": "Client Address",
                    "required": False,
                    "value_type": "string",
                },
            ],
        }
    ]
    current_result = normalize_extraction_result(
        template_modules=template_modules,
        raw_result={
            "modules": [
                {
                    "key": "parties",
                    "fields": [
                        {
                            "key": "client_name",
                            "value": "Maison Habitat",
                            "confidence": 0.88,
                            "extraction_mode": "direct",
                        },
                        {
                            "key": "client_address",
                            "value": "12 Old Street",
                            "confidence": 0.72,
                            "extraction_mode": "direct",
                        },
                    ],
                }
            ]
        },
    )

    corrected = apply_extraction_corrections(
        template_modules=template_modules,
        current_result=current_result,
        raw_updates={
            "modules": [
                {
                    "key": "parties",
                    "fields": [
                        {
                            "key": "client_address",
                            "value": "42 New Street",
                            "confidence": 0.95,
                            "extraction_mode": "direct",
                            "evidence": {
                                "source_chunk_indices": [],
                                "source_excerpt": "Operator correction: 42 New Street",
                            },
                        }
                    ],
                }
            ]
        },
    )

    client_name = corrected.modules[0].fields[0]
    client_address = corrected.modules[0].fields[1]

    assert client_name.value == "Maison Habitat"
    assert client_address.value == "42 New Street"
    assert client_address.confidence == 0.95


def test_correction_finalizer_draft_normalizes_empty_list_updates() -> None:
    draft = CorrectionFinalizerDraft.model_validate(
        {
            "assistant_response": "No change was required.",
            "reasoning_summary": "The current draft already matches the requested value.",
            "updates": [],
        }
    )

    assert draft.updates.modules == []


def test_correction_finalizer_draft_wraps_module_list_updates() -> None:
    draft = CorrectionFinalizerDraft.model_validate(
        {
            "assistant_response": "I updated the client address.",
            "reasoning_summary": "The operator supplied the corrected address directly.",
            "updates": [
                {
                    "key": "parties",
                    "fields": [
                        {
                            "key": "client_address",
                            "value": "42 New Street",
                            "confidence": 1,
                            "extraction_mode": "direct",
                        }
                    ],
                }
            ],
        }
    )

    assert len(draft.updates.modules) == 1
    assert draft.updates.modules[0].key == "parties"
    assert draft.updates.modules[0].fields[0].key == "client_address"

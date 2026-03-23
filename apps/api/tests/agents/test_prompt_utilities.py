from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agents.document_extraction_agent.graph import (
    _build_evidence_transcript as build_extraction_evidence_transcript,
)
from src.agents.document_extraction_correction_agent.graph import (
    _build_evidence_transcript as build_correction_evidence_transcript,
)
from src.agents.prompt_utils import build_template_field_guide


def test_build_template_field_guide_renders_scalars_and_tables() -> None:
    guide = build_template_field_guide(
        [
            {
                "key": "invoice_overview",
                "label": "Invoice Overview",
                "fields": [
                    {
                        "key": "invoice_number",
                        "label": "Invoice Number",
                        "required": True,
                        "description": "Supplier invoice reference.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "invoice_items",
                        "label": "Invoice Items",
                        "required": False,
                        "description": "Billed rows.",
                        "kind": "table",
                        "min_rows": 1,
                        "columns": [
                            {
                                "key": "description",
                                "value_type": "string",
                                "required": True,
                            },
                            {
                                "key": "line_total",
                                "value_type": "number",
                                "required": True,
                            },
                        ],
                    },
                ],
            }
        ]
    )

    assert "Module invoice_overview (Invoice Overview)" in guide
    assert (
        "- invoice_overview.invoice_number | scalar<string> | required | Invoice Number"
        in guide
    )
    assert "- invoice_overview.invoice_items | table | optional | Invoice Items" in guide
    assert "columns: description<string> required, line_total<number> required" in guide


def test_extraction_evidence_transcript_uses_only_tool_messages() -> None:
    transcript = build_extraction_evidence_transcript(
        [
            HumanMessage(content="search for invoice number"),
            AIMessage(content="I will check the totals next."),
            ToolMessage(
                content='{"results":[{"chunk_index":3,"excerpt":"Invoice No. INV-2048"}]}',
                tool_call_id="call-1",
                name="keyword_search",
            ),
        ]
    )

    assert "[human]" not in transcript
    assert "[assistant]" not in transcript
    assert "[tool:keyword_search]" in transcript
    assert "INV-2048" in transcript


def test_correction_evidence_transcript_uses_only_tool_messages() -> None:
    transcript = build_correction_evidence_transcript(
        [
            HumanMessage(content="fix the total amount"),
            AIMessage(content="I found a likely value."),
            ToolMessage(
                content='{"results":[{"chunk_index":7,"excerpt":"Total due: 1820.50"}]}',
                tool_call_id="call-2",
                name="inspect_chunk",
            ),
        ]
    )

    assert "[human]" not in transcript
    assert "[assistant]" not in transcript
    assert "[tool:inspect_chunk]" in transcript
    assert "1820.50" in transcript

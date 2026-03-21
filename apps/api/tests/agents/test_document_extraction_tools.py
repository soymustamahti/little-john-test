from src.agents.document_extraction_agent.tools import TOOLS


def test_retrieval_tools_hide_document_id_from_model_schema() -> None:
    schemas_by_name = {
        tool.name: tool.tool_call_schema.model_json_schema()
        for tool in TOOLS
    }

    assert schemas_by_name["hybrid_search"]["properties"].keys() == {"query", "top_k"}
    assert schemas_by_name["keyword_search"]["properties"].keys() == {"query", "top_k"}
    assert schemas_by_name["semantic_search"]["properties"].keys() == {"query", "top_k"}
    assert schemas_by_name["inspect_chunk"]["properties"].keys() == {"chunk_index"}
    assert schemas_by_name["inspect_spreadsheet"]["properties"].keys() == {
        "sheet_name",
        "max_rows",
    }

    for schema in schemas_by_name.values():
        assert "document_id" not in schema["properties"]

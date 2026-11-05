from backend.app.rag.parsing import safe_parse_llm_json
from backend.app.schemas.chat import CatalogFilterSchema


def test_safe_parser_handles_markdown_and_invalid_output() -> None:
    default = CatalogFilterSchema()
    parsed = safe_parse_llm_json(
        'Here is the result: ```json {"department": "Men"} ```',
        CatalogFilterSchema,
        default,
    )
    assert parsed.department == "Men"
    assert safe_parse_llm_json("not json", CatalogFilterSchema, default) == default

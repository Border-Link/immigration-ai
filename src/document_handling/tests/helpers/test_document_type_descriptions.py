import pytest


@pytest.mark.django_db
class TestDocumentTypeDescriptions:
    def test_get_document_type_description_known(self):
        from document_handling.helpers.document_type_descriptions import get_document_type_description

        info = get_document_type_description("passport")
        assert isinstance(info, dict)
        assert "description" in info
        assert "key_indicators" in info
        assert isinstance(info["key_indicators"], list)
        assert len(info["key_indicators"]) > 0

    def test_get_document_type_description_unknown_is_defensive(self):
        from document_handling.helpers.document_type_descriptions import get_document_type_description

        info = get_document_type_description("SOME_UNKNOWN_TYPE")
        assert isinstance(info, dict)
        assert "Document type" in info["description"]
        assert info["key_indicators"] == []

    def test_format_document_types_for_prompt_empty(self):
        from document_handling.helpers.document_type_descriptions import format_document_types_for_prompt

        assert format_document_types_for_prompt([]) == "No document types available."

    def test_format_document_types_for_prompt_renders_bullets(self):
        from document_handling.helpers.document_type_descriptions import format_document_types_for_prompt

        s = format_document_types_for_prompt(["PASSPORT", "BANK_STATEMENT"])
        assert "- **PASSPORT**:" in s
        assert "- **BANK_STATEMENT**:" in s

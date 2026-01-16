import pytest


@pytest.mark.unit
class TestPrompts:
    def test_get_jurisdiction_name_known_and_unknown(self):
        from data_ingestion.helpers.prompts import get_jurisdiction_name

        assert get_jurisdiction_name("UK") == "United Kingdom"
        assert get_jurisdiction_name("US") == "United States"
        assert get_jurisdiction_name("XX") == "XX"

    def test_system_message_includes_jurisdiction_and_json_logic_examples(self):
        from data_ingestion.helpers.prompts import get_rule_extraction_system_message

        msg = get_rule_extraction_system_message("United Kingdom")
        assert "United Kingdom" in msg
        assert "JSON LOGIC" in msg
        # Ensure the brace-escaping produced real JSON-ish examples, not literal '{{'
        assert '{"var": "salary"}' in msg
        assert '"requirements"' in msg

    def test_user_prompt_includes_extracted_text_and_uk_currency_example(self):
        from data_ingestion.helpers.prompts import get_rule_extraction_user_prompt

        extracted_text = "Applicants must earn at least £38,700 per year."
        prompt = get_rule_extraction_user_prompt(
            jurisdiction_name="United Kingdom",
            jurisdiction="UK",
            extracted_text=extracted_text,
        )
        assert extracted_text in prompt
        assert "£38,700" in prompt
        assert '"visa_code"' in prompt

import pytest

from data_ingestion.services.rule_parsing.response_parser import ResponseParser


class TestResponseParser:
    def test_parse_llm_response_direct_json(self):
        parsed = ResponseParser.parse_llm_response('{"visa_code":"UK","requirements":[]}')
        assert parsed["visa_code"] == "UK"

    def test_parse_llm_response_markdown_wrapped(self):
        raw = "Here you go:\n```json\n{\"visa_code\":\"UK\",\"requirements\":[]}\n```"
        parsed = ResponseParser.parse_llm_response(raw)
        assert parsed["visa_code"] == "UK"

    def test_parse_llm_response_empty(self):
        assert ResponseParser.parse_llm_response("") is None
        assert ResponseParser.parse_llm_response("   ") is None

    def test_extract_rules_from_response_requirements_list(self):
        parsed = {"visa_code": "UK", "requirements": [{"requirement_code": "FEE", "description": "Pay fee", "condition_expression": {"==": [1, 1]}, "source_excerpt": "Fee"}]}
        rules = ResponseParser.extract_rules_from_response(parsed)
        assert len(rules) == 1
        assert rules[0]["visa_code"] == "UK"
        assert rules[0]["requirement_code"] == "FEE"

    def test_extract_rules_from_response_single_rule_object(self):
        parsed = {"visa_code": "UK", "requirement_code": "DOC", "description": "Provide doc", "condition_expression": {"==": [1, 1]}, "source_excerpt": "Doc"}
        rules = ResponseParser.extract_rules_from_response(parsed)
        assert len(rules) == 1
        assert rules[0]["requirement_code"] == "DOC"

    def test_extract_rules_from_response_invalid_formats(self):
        rules = ResponseParser.extract_rules_from_response({"visa_code": "UK", "requirements": "not-a-list"})
        assert isinstance(rules, list)


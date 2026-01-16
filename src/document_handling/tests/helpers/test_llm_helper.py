"""
Tests for document_handling.helpers.llm_helper.
"""

import pytest

from document_handling.helpers.llm_helper import parse_llm_json_response


@pytest.mark.django_db
class TestLLMHelper:
    def test_parse_llm_json_response_plain_json(self):
        obj = parse_llm_json_response('{"a": 1}')
        assert obj == {"a": 1}

    def test_parse_llm_json_response_markdown_fence(self):
        content = "```json\n{\n  \"a\": 1\n}\n```"
        obj = parse_llm_json_response(content)
        assert obj == {"a": 1}

    def test_parse_llm_json_response_invalid_returns_none(self):
        obj = parse_llm_json_response("not-json")
        assert obj is None


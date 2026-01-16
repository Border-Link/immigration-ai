import pytest


@pytest.mark.unit
class TestRuleParsingConstants:
    def test_basic_invariants(self):
        from data_ingestion.helpers import rule_parsing_constants as c

        assert isinstance(c.DEFAULT_LLM_MODEL, str) and c.DEFAULT_LLM_MODEL
        assert isinstance(c.FALLBACK_LLM_MODEL, str) and c.FALLBACK_LLM_MODEL
        assert c.LLM_TIMEOUT_SECONDS > 0
        assert c.MIN_TEXT_LENGTH > 0
        assert c.MAX_TEXT_LENGTH > c.MIN_TEXT_LENGTH

    def test_json_logic_operators_contains_expected_core_ops(self):
        from data_ingestion.helpers import rule_parsing_constants as c

        # These are foundational operators used in prompts/validation
        assert "and" in c.VALID_JSON_LOGIC_OPERATORS
        assert ">=" in c.VALID_JSON_LOGIC_OPERATORS
        assert "var" in c.VALID_JSON_LOGIC_OPERATORS

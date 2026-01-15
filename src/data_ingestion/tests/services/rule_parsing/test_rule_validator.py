import pytest

from data_ingestion.services.rule_parsing.rule_validator import RuleValidator


class TestRuleValidator:
    def test_validate_rule_data_missing_required_fields(self):
        result = RuleValidator.validate_rule_data({})
        assert result["valid"] is False
        assert "Missing required field" in result["error"]

    def test_validate_rule_data_invalid_types(self):
        result = RuleValidator.validate_rule_data("not-a-dict")  # type: ignore[arg-type]
        assert result["valid"] is False

    def test_validate_rule_data_valid_minimal(self):
        rule = {
            "visa_code": "UK",
            "requirement_code": "FEE_PAYMENT",
            "description": "Applicant must pay the fee.",
            "condition_expression": {"==": [{"var": "fee_paid"}, True]},
            "source_excerpt": "Fee is required",
        }
        result = RuleValidator.validate_rule_data(rule)
        assert result["valid"] is True

    def test_validate_rule_data_rejects_short_description(self):
        rule = {
            "visa_code": "UK",
            "requirement_code": "FEE_PAYMENT",
            "description": "short",
            "condition_expression": {"==": [{"var": "fee_paid"}, True]},
            "source_excerpt": "Fee is required",
        }
        result = RuleValidator.validate_rule_data(rule)
        assert result["valid"] is False
        assert "description must be at least" in result["error"]

    def test_validate_requirement_code_format(self):
        assert RuleValidator._validate_requirement_code_format("VALID_CODE_1") is True
        assert RuleValidator._validate_requirement_code_format("_INVALID") is False
        assert RuleValidator._validate_requirement_code_format("invalid") is False
        assert RuleValidator._validate_requirement_code_format("BAD__CODE") is False

    def test_validate_json_logic_comprehensive_depth_warning(self):
        expr = {"and": [{"and": [{"and": [{"and": [{"and": [{"and": [{"and": [{"and": [{"==": [1, 1]}]}]}]}]}]}]}]}]}
        ok, err, warnings = RuleValidator.validate_json_logic_comprehensive(expr)
        assert ok is True
        assert err is None
        assert isinstance(warnings, list)

    def test_infer_rule_type_fee_from_description(self):
        rule = {"requirement_code": "OTHER", "description": "Pay the fee", "condition_expression": {"==": [1, 1]}, "source_excerpt": "Fee"}
        inferred = RuleValidator.infer_rule_type(rule)
        assert inferred == "fee"


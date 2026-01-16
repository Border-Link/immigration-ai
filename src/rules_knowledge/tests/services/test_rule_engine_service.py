"""
Tests for RuleEngineService pure evaluation logic.

We avoid cross-app DB dependencies by focusing on deterministic methods:
- validate_expression_structure
- extract_variables_from_expression
- evaluate_expression
- evaluate_requirement (with an in-memory requirement instance)
- aggregate_results
"""

import pytest

from rules_knowledge.services.rule_engine_service import RuleEngineService, RuleEngineEvaluationResult


@pytest.mark.django_db
class TestRuleEngineServicePure:
    def test_validate_expression_structure(self):
        ok, err = RuleEngineService.validate_expression_structure(None)
        assert ok is False
        assert "None" in err

        ok, err = RuleEngineService.validate_expression_structure("not-a-dict")
        assert ok is False
        assert "dict or list" in err

        ok, err = RuleEngineService.validate_expression_structure({})
        assert ok is False

        ok, err = RuleEngineService.validate_expression_structure([])
        assert ok is False

        ok, err = RuleEngineService.validate_expression_structure({">=": [{"var": "age"}, 18]})
        assert ok is True
        assert err is None

    def test_extract_variables_from_expression(self):
        expr = {
            "and": [
                {">=": [{"var": "age"}, 18]},
                {"==": [{"var": "country"}, "UK"]},
                {"or": [{"var": "has_sponsor"}, {"var": "has_job_offer"}]},
            ]
        }
        vars_ = RuleEngineService.extract_variables_from_expression(expr)
        assert set(vars_) == {"age", "country", "has_sponsor", "has_job_offer"}

    def test_evaluate_expression_missing_facts(self):
        expr = {">=": [{"var": "age"}, 18]}
        out = RuleEngineService.evaluate_expression(expr, case_facts={})
        assert out["passed"] is False
        assert out["missing_facts"] == ["age"]
        assert out["error"] is None

    def test_evaluate_expression_constant_expression(self):
        out = RuleEngineService.evaluate_expression({"==": [1, 1]}, case_facts={})
        assert out["passed"] is True
        assert out["missing_facts"] == []
        assert out["error"] is None

    def test_evaluate_expression_success(self):
        expr = {">=": [{"var": "salary"}, 30000]}
        out = RuleEngineService.evaluate_expression(expr, case_facts={"salary": 40000})
        assert out["passed"] is True
        assert out["missing_facts"] == []
        assert out["error"] is None

    def test_evaluate_expression_division_by_zero_is_handled(self):
        expr = {"/": [1, 0]}
        out = RuleEngineService.evaluate_expression(expr, case_facts={})
        # json_logic can raise; service should convert to error
        assert out["passed"] is False
        assert out["error"] is not None

    def test_evaluate_requirement_missing_facts(self, visa_requirement):
        # use a valid requirement and provide empty facts
        out = RuleEngineService.evaluate_requirement(visa_requirement, case_facts={})
        assert out["passed"] is False
        assert out["missing_facts"] == ["age"]
        assert out["error"] is None

    def test_evaluate_requirement_invalid_expression_structure(self, visa_requirement):
        # mutate in-memory only (do not save)
        visa_requirement.condition_expression = None
        out = RuleEngineService.evaluate_requirement(visa_requirement, case_facts={"age": 30})
        assert out["passed"] is False
        assert out["error"] is not None

    def test_aggregate_results_empty(self, rule_version_unpublished):
        result = RuleEngineService.aggregate_results([], rule_version_unpublished)
        assert isinstance(result, RuleEngineEvaluationResult)
        assert result.outcome == "unlikely"
        assert result.confidence == 0.0
        assert "No requirements found" in " ".join(result.warnings)

    def test_aggregate_results_all_missing_facts(self, rule_version_unpublished):
        evals = [
            {"requirement_code": "R1", "passed": False, "missing_facts": ["x"], "error": None, "is_mandatory": True},
            {"requirement_code": "R2", "passed": False, "missing_facts": ["y"], "error": None, "is_mandatory": True},
        ]
        result = RuleEngineService.aggregate_results(evals, rule_version_unpublished)
        assert result.outcome == "unlikely"
        assert result.requirements_with_missing_facts == 2
        assert set(result.missing_facts) == {"x", "y"}

    def test_aggregate_results_mandatory_failure_downgrades(self, rule_version_unpublished):
        evals = [
            {"requirement_code": "R1", "passed": True, "missing_facts": [], "error": None, "is_mandatory": True},
            {"requirement_code": "R2", "passed": False, "missing_facts": [], "error": None, "is_mandatory": True},
            {"requirement_code": "R3", "passed": True, "missing_facts": [], "error": None, "is_mandatory": False},
            {"requirement_code": "R4", "passed": True, "missing_facts": [], "error": None, "is_mandatory": False},
        ]
        result = RuleEngineService.aggregate_results(evals, rule_version_unpublished)
        # With a mandatory failure, should not be "likely"
        assert result.outcome in ("possible", "unlikely")
        assert result.requirements_failed >= 1


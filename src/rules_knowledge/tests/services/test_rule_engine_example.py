"""
Tests for rule_engine_example module.

These are smoke tests to ensure the example functions call RuleEngineService as intended,
without invoking cross-app DB dependencies.
"""

from unittest.mock import patch, MagicMock

import pytest


@pytest.mark.django_db
class TestRuleEngineExample:
    def test_example_eligibility_check_calls_service(self):
        from rules_knowledge.services import rule_engine_example

        fake_result = MagicMock()
        fake_result.outcome = "possible"
        fake_result.confidence = 0.5
        fake_result.requirements_passed = 1
        fake_result.requirements_total = 2
        fake_result.missing_facts = []
        fake_result.to_dict.return_value = {"outcome": "possible"}

        with patch.object(rule_engine_example.RuleEngineService, "run_eligibility_evaluation", return_value=fake_result) as run:
            out = rule_engine_example.example_eligibility_check()
            assert out == {"outcome": "possible"}
            run.assert_called_once()

    def test_example_step_by_step_calls_service_methods(self):
        from rules_knowledge.services import rule_engine_example

        with (
            patch.object(rule_engine_example.RuleEngineService, "load_case_facts", return_value={"age": 30}) as load_facts,
            patch.object(rule_engine_example.RuleEngineService, "load_active_rule_version", return_value=MagicMock(id="rv", effective_from="now")) as load_rv,
            patch.object(rule_engine_example.RuleEngineService, "evaluate_all_requirements", return_value=[]) as eval_all,
            patch.object(rule_engine_example.RuleEngineService, "aggregate_results", return_value=MagicMock(outcome="unlikely", confidence=0.0)) as agg,
        ):
            rule_engine_example.example_step_by_step()
            load_facts.assert_called_once()
            load_rv.assert_called_once()
            eval_all.assert_called_once()
            agg.assert_called_once()


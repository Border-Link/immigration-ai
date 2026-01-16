from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_decisions.services.eligibility_check_service import EligibilityCheckService


@pytest.mark.django_db
class TestEligibilityCheckService:
    def test_case_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=None),
        )
        result = EligibilityCheckService.run_eligibility_check(case_id="missing", visa_type_id="vt")
        assert result.success is False
        assert "not found" in (result.error or "").lower()

    def test_payment_validation_blocks(self, monkeypatch, paid_case):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(False, "payment required")),
        )
        result = EligibilityCheckService.run_eligibility_check(case_id=str(case.id), visa_type_id="vt")
        assert result.success is False
        assert result.error == "payment required"
        assert "Payment validation failed" in result.warnings

    def test_visa_type_not_found(self, monkeypatch, paid_case):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.VisaTypeSelector.get_by_id",
            MagicMock(return_value=None),
        )
        result = EligibilityCheckService.run_eligibility_check(case_id=str(case.id), visa_type_id="vt")
        assert result.success is False
        assert "visa type" in (result.error or "").lower()

    def test_case_has_no_facts(self, monkeypatch, paid_case, visa_type):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.VisaTypeSelector.get_by_id",
            MagicMock(return_value=visa_type),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.load_case_facts",
            MagicMock(return_value=None),
        )
        result = EligibilityCheckService.run_eligibility_check(case_id=str(case.id), visa_type_id=str(visa_type.id))
        assert result.success is False
        assert "no facts" in (result.error or "").lower()

    def test_rule_engine_returns_none(self, monkeypatch, paid_case, visa_type):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.VisaTypeSelector.get_by_id",
            MagicMock(return_value=visa_type),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.load_case_facts",
            MagicMock(return_value={"age": 30}),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.run_eligibility_evaluation",
            MagicMock(return_value=None),
        )
        result = EligibilityCheckService.run_eligibility_check(case_id=str(case.id), visa_type_id=str(visa_type.id))
        assert result.success is False
        assert "rule engine" in (result.error or "").lower()

    def test_ai_disabled_uses_rule_engine_only_and_stores_result(self, monkeypatch, paid_case, visa_type, rule_version):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.VisaTypeSelector.get_by_id",
            MagicMock(return_value=visa_type),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.load_case_facts",
            MagicMock(return_value={"age": 30, "visa_type": visa_type.code}),
        )

        rule_engine_result = SimpleNamespace(
            outcome="likely",
            confidence=0.8,
            warnings=[],
            missing_facts=[],
            requirements_passed=3,
            requirements_total=3,
            rule_version_id=str(rule_version.id),
            to_dict=lambda: {"outcome": "likely", "confidence": 0.8, "requirements": []},
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.run_eligibility_evaluation",
            MagicMock(return_value=rule_engine_result),
        )

        # Avoid actual create_eligibility_result (signals etc.) for this unit test.
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.EligibilityCheckService._store_eligibility_result",
            MagicMock(return_value=SimpleNamespace(id="er1")),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.EligibilityCheckService._escalate_to_human_review",
            MagicMock(return_value=None),
        )

        result = EligibilityCheckService.run_eligibility_check(
            case_id=str(case.id),
            visa_type_id=str(visa_type.id),
            enable_ai_reasoning=False,
        )
        assert result.success is True
        assert result.outcome in {"likely", "possible", "unlikely"}
        assert result.eligibility_result_id == "er1"

    def test_ai_conflict_triggers_human_review(self, monkeypatch, paid_case, visa_type, rule_version):
        case, _payment = paid_case
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.CaseSelector.get_by_id",
            MagicMock(return_value=case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.VisaTypeSelector.get_by_id",
            MagicMock(return_value=visa_type),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.load_case_facts",
            MagicMock(return_value={"age": 30, "visa_type": visa_type.code}),
        )

        rule_engine_result = SimpleNamespace(
            outcome="unlikely",
            confidence=0.9,
            warnings=[],
            missing_facts=[],
            requirements_passed=0,
            requirements_total=3,
            rule_version_id=str(rule_version.id),
            to_dict=lambda: {"outcome": "unlikely", "confidence": 0.9, "requirements": []},
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.RuleEngineService.run_eligibility_evaluation",
            MagicMock(return_value=rule_engine_result),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.AIReasoningService.run_ai_reasoning",
            MagicMock(return_value={"success": True, "response": "This looks likely eligible.", "reasoning_log_id": "log1"}),
        )
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.EligibilityCheckService._store_eligibility_result",
            MagicMock(return_value=SimpleNamespace(id="er1")),
        )
        escalate = MagicMock(return_value=SimpleNamespace(id="rev1"))
        monkeypatch.setattr(
            "ai_decisions.services.eligibility_check_service.EligibilityCheckService._escalate_to_human_review",
            escalate,
        )

        result = EligibilityCheckService.run_eligibility_check(case_id=str(case.id), visa_type_id=str(visa_type.id))
        assert result.success is True
        assert result.conflict_detected is True
        assert result.requires_human_review is True
        assert result.outcome == "possible"
        assert escalate.call_count == 1


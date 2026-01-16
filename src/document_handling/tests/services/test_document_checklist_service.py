"""
Tests for DocumentChecklistService.

We mock rules_knowledge selectors and rule engine evaluation to deterministically
cover:
- payment required paths
- missing visa_type/rule_version
- conditional logic evaluation and default behavior on evaluation issues
"""

import pytest

from document_handling.services.document_checklist_service import DocumentChecklistService


@pytest.mark.django_db
class TestDocumentChecklistService:
    def test_generate_checklist_payment_required_returns_error_shape(self, monkeypatch):
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.CaseSelector.get_by_id",
            lambda *_: object(),
            raising=True,
        )
        result = DocumentChecklistService.generate_checklist("case-id")
        assert isinstance(result, dict)
        assert result.get("requirements") == []
        assert "error" in result

    def test_generate_checklist_case_has_no_visa_type(self, monkeypatch):
        case = type("Case", (), {"id": "c", "visa_type": None})()
        monkeypatch.setattr("document_handling.services.document_checklist_service.CaseSelector.get_by_id", lambda *_: case, raising=True)
        result = DocumentChecklistService.generate_checklist("case-id")
        assert result.get("requirements") == []
        assert result.get("summary", {}).get("total_required") == 0

    def test_generate_checklist_no_rule_version(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "TestVisa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        monkeypatch.setattr("document_handling.services.document_checklist_service.CaseSelector.get_by_id", lambda *_: case, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: None,
            raising=True,
        )
        result = DocumentChecklistService.generate_checklist("case-id")
        assert result.get("requirements") == []
        assert result.get("visa_type", {}).get("name") == "TestVisa"

    def test_generate_checklist_conditional_logic_not_applies_skips_requirement(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "TestVisa"})()
        rv = type("RV", (), {"id": "rv", "version": "1", "effective_from": None})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()

        dt = type("DT", (), {"id": "dt1", "name": "Passport", "code": "passport"})()
        req = type("Req", (), {"id": "r1", "document_type": dt, "mandatory": True, "conditional_logic": "age > 18"})()

        class _Reqs(list):
            def exists(self):
                return True

        monkeypatch.setattr("document_handling.services.document_checklist_service.CaseSelector.get_by_id", lambda *_: case, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Reqs([req]),
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.CaseDocumentSelector.get_by_filters",
            lambda *_args, **_kwargs: [],
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.RuleEngineService.load_case_facts",
            lambda *_: {"age": 17},
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.RuleEngineService.evaluate_expression",
            lambda *_args, **_kwargs: {"passed": False, "result": False, "error": None, "missing_facts": []},
            raising=True,
        )
        result = DocumentChecklistService.generate_checklist("case-id")
        assert result.get("requirements") == []
        assert result.get("summary", {}).get("total_required") == 0

    def test_generate_checklist_conditional_eval_error_defaults_to_applies(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "TestVisa"})()
        rv = type("RV", (), {"id": "rv", "version": "1", "effective_from": None})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()

        dt = type("DT", (), {"id": "dt1", "name": "Passport", "code": "passport"})()
        req = type("Req", (), {"id": "r1", "document_type": dt, "mandatory": True, "conditional_logic": "age > 18"})()

        class _Reqs(list):
            def exists(self):
                return True

        monkeypatch.setattr("document_handling.services.document_checklist_service.CaseSelector.get_by_id", lambda *_: case, raising=True)
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Reqs([req]),
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.CaseDocumentSelector.get_by_filters",
            lambda *_args, **_kwargs: [],
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.RuleEngineService.load_case_facts",
            lambda *_: {"age": None},
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_checklist_service.RuleEngineService.evaluate_expression",
            lambda *_args, **_kwargs: {"passed": False, "result": False, "error": "bad expr", "missing_facts": ["age"]},
            raising=True,
        )
        result = DocumentChecklistService.generate_checklist("case-id")
        assert result.get("summary", {}).get("total_required") == 1
        assert result["requirements"][0]["status"] == "missing"


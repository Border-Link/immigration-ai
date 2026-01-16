"""
Tests for DocumentRequirementMatchingService.

We mock selectors/rule engine to cover:
- payment required
- missing visa type / missing rule version / missing requirements
- missing document type
- mismatch vs match and conditional logic behavior
"""

import pytest

from document_handling.services.document_requirement_matching_service import DocumentRequirementMatchingService


@pytest.mark.django_db
class TestDocumentRequirementMatchingService:
    def test_match_document_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: None,
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("missing")
        assert result == "failed"
        assert err is not None

    def test_match_document_payment_required(self, monkeypatch):
        case = type("Case", (), {"id": "c", "visa_type": None})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": None})()
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        from payments.helpers import payment_validator

        monkeypatch.setattr(
            payment_validator.PaymentValidator,
            "validate_case_has_payment",
            lambda *args, **kwargs: (False, "payment required"),
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "failed"
        assert details.get("payment_required") is True

    def test_match_document_case_has_no_visa_type(self, monkeypatch):
        case = type("Case", (), {"id": "c", "visa_type": None})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": None})()
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "pending"

    def test_match_document_no_rule_version(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "Visa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": None})()
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: None,
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "pending"

    def test_match_document_no_requirements(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "Visa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": None})()
        rv = type("RV", (), {"id": "rv"})()

        class _Empty(list):
            def exists(self):
                return False

        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Empty(),
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "pending"

    def test_match_document_missing_document_type(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "Visa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": None})()
        rv = object()

        class _Reqs(list):
            def exists(self):
                return True

        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Reqs([object()]),
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "warning"
        assert details.get("requires_classification") is True

    def test_match_document_type_not_in_requirements_fails(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "Visa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        dt = type("DT", (), {"id": "dt", "name": "Passport", "code": "passport"})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": dt})()
        rv = object()

        req_dt = type("DT", (), {"id": "dt2", "name": "Bank", "code": "bank"})()
        req = type("Req", (), {"id": "r", "document_type": req_dt, "mandatory": True, "conditional_logic": None})()

        class _Reqs(list):
            def exists(self):
                return True

        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Reqs([req]),
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "failed"
        assert "required_document_types" in details

    def test_match_document_requirement_matches_and_conditional_passed(self, monkeypatch):
        visa = type("Visa", (), {"id": "v", "name": "Visa"})()
        case = type("Case", (), {"id": "c", "visa_type": visa})()
        dt = type("DT", (), {"id": "dt", "name": "Passport", "code": "passport"})()
        doc = type("Doc", (), {"id": "d", "case": case, "document_type": dt})()
        rv = object()
        req = type("Req", (), {"id": "r", "document_type": dt, "mandatory": True, "conditional_logic": "age>18"})()

        class _Reqs(list):
            def exists(self):
                return True

        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.CaseDocumentSelector.get_by_id",
            lambda *_: doc,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaRuleVersionSelector.get_current_by_visa_type",
            lambda *_: rv,
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.VisaDocumentRequirementSelector.get_by_rule_version",
            lambda *_: _Reqs([req]),
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.RuleEngineService.load_case_facts",
            lambda *_: {"age": 20},
            raising=True,
        )
        monkeypatch.setattr(
            "document_handling.services.document_requirement_matching_service.RuleEngineService.evaluate_expression",
            lambda *_a, **_k: {"passed": True, "result": True, "error": None, "missing_facts": []},
            raising=True,
        )
        result, details, err = DocumentRequirementMatchingService.match_document_against_requirements("d")
        assert result == "passed"
        assert err is None


"""
API tests for case eligibility endpoints.

These endpoints orchestrate across AI/rules/document modules; tests isolate external dependencies
and focus on request validation, permissions, and response formatting.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from rest_framework import status


BASE = "/api/v1/imigration-cases"


@pytest.mark.django_db
class TestCaseEligibilityEndpoints:
    def test_eligibility_requires_reviewer_or_admin(self, api_client, case_owner, draft_case):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/cases/{draft_case.id}/eligibility/", {}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_eligibility_invalid_visa_type_ids_format(self, api_client, reviewer_user, draft_case):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{BASE}/cases/{draft_case.id}/eligibility/",
            {"visa_type_ids": "not-a-list"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_eligibility_too_many_visa_types(self, api_client, reviewer_user, draft_case):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{BASE}/cases/{draft_case.id}/eligibility/",
            {"visa_type_ids": [str(uuid.uuid4()) for _ in range(11)]},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_eligibility_invalid_visa_type_uuid_in_list(self, api_client, reviewer_user, draft_case):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{BASE}/cases/{draft_case.id}/eligibility/",
            {"visa_type_ids": ["not-a-uuid"]},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_eligibility_enable_ai_reasoning_must_be_boolean(self, api_client, reviewer_user, draft_case):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{BASE}/cases/{draft_case.id}/eligibility/",
            {"enable_ai_reasoning": "true"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_eligibility_no_active_visa_types_returns_400(self, monkeypatch, api_client, reviewer_user, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=reviewer_user)

        from rules_knowledge.selectors import visa_type_selector as visa_type_selector_module

        monkeypatch.setattr(visa_type_selector_module.VisaTypeSelector, "get_by_jurisdiction", MagicMock(return_value=[]))
        resp = api_client.post(f"{BASE}/cases/{case.id}/eligibility/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_eligibility_success_with_mocked_dependencies(self, monkeypatch, api_client, reviewer_user, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=reviewer_user)

        # Mock visa type selection
        from rules_knowledge.selectors import visa_type_selector as visa_type_selector_module

        vt = MagicMock()
        vt.id = "11111111-1111-1111-1111-111111111111"
        vt.code = "VT1"
        vt.name = "Visa Type 1"

        monkeypatch.setattr(visa_type_selector_module.VisaTypeSelector, "get_by_jurisdiction", MagicMock(return_value=[vt]))
        monkeypatch.setattr(visa_type_selector_module.VisaTypeSelector, "get_by_id", MagicMock(return_value=vt))

        # Mock eligibility check service output
        from ai_decisions.services import eligibility_check_service as eligibility_check_service_module

        rule_engine_result = MagicMock()
        rule_engine_result.requirements_passed = 1
        rule_engine_result.requirements_total = 2
        rule_engine_result.requirements_failed = 1
        rule_engine_result.requirements_with_missing_facts = 0
        rule_engine_result.missing_facts = []
        rule_engine_result.requirement_details = [
            {"requirement_code": "R1", "description": "Req 1", "passed": False, "missing_facts": [], "error": None}
        ]

        check_result = MagicMock()
        check_result.success = True
        check_result.outcome = "likely"
        check_result.confidence = 0.9
        check_result.eligibility_result_id = None
        check_result.rule_engine_result = rule_engine_result
        check_result.requires_human_review = False
        check_result.reasoning_summary = "ok"
        check_result.warnings = []

        monkeypatch.setattr(
            eligibility_check_service_module.EligibilityCheckService,
            "run_eligibility_check",
            MagicMock(return_value=check_result),
        )
        monkeypatch.setattr(eligibility_check_service_module.EligibilityCheckService, "LOW_CONFIDENCE_THRESHOLD", 0.5)

        resp = api_client.post(f"{BASE}/cases/{case.id}/eligibility/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["case_id"] == str(case.id)
        assert resp.data["data"]["results"]

    def test_eligibility_partial_failures_returns_207(self, monkeypatch, api_client, reviewer_user, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=reviewer_user)

        from rules_knowledge.selectors import visa_type_selector as visa_type_selector_module
        from ai_decisions.services import eligibility_check_service as eligibility_check_service_module

        vt = MagicMock()
        vt.id = "11111111-1111-1111-1111-111111111111"
        vt.code = "VT1"
        vt.name = "Visa Type 1"

        def _get_by_id(visa_type_id):
            return vt if str(visa_type_id) == str(vt.id) else None

        monkeypatch.setattr(visa_type_selector_module.VisaTypeSelector, "get_by_id", MagicMock(side_effect=_get_by_id))

        rule_engine_result = MagicMock()
        rule_engine_result.requirements_passed = 1
        rule_engine_result.requirements_total = 1
        rule_engine_result.requirements_failed = 0
        rule_engine_result.requirements_with_missing_facts = 0
        rule_engine_result.missing_facts = []
        rule_engine_result.requirement_details = []

        check_result = MagicMock()
        check_result.success = True
        check_result.outcome = "likely"
        check_result.confidence = 0.9
        check_result.eligibility_result_id = None
        check_result.rule_engine_result = rule_engine_result
        check_result.requires_human_review = False
        check_result.reasoning_summary = "ok"
        check_result.warnings = []

        monkeypatch.setattr(
            eligibility_check_service_module.EligibilityCheckService,
            "run_eligibility_check",
            MagicMock(return_value=check_result),
        )
        monkeypatch.setattr(eligibility_check_service_module.EligibilityCheckService, "LOW_CONFIDENCE_THRESHOLD", 0.5)

        resp = api_client.post(
            f"{BASE}/cases/{case.id}/eligibility/",
            {"visa_type_ids": [str(vt.id), str(uuid.uuid4())]},
            format="json",
        )
        assert resp.status_code == status.HTTP_207_MULTI_STATUS
        assert resp.data["data"]["results"]
        assert resp.data["data"]["errors"]


@pytest.mark.django_db
class TestCaseEligibilityExplanationEndpoints:
    def test_explanation_requires_auth(self, api_client, draft_case):
        resp = api_client.get(
            f"{BASE}/cases/{draft_case.id}/eligibility/{uuid.uuid4()}/explanation/",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_explanation_owner_success_with_mocked_dependencies(self, monkeypatch, api_client, case_owner, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)

        result_id = uuid.uuid4()
        eligibility_result = MagicMock()
        eligibility_result.id = result_id
        eligibility_result.case = case
        eligibility_result.rule_version = None
        eligibility_result.reasoning_summary = "ok"

        from ai_decisions.selectors import eligibility_result_selector as eligibility_result_selector_module
        from ai_decisions.selectors import ai_reasoning_log_selector as ai_reasoning_log_selector_module

        monkeypatch.setattr(
            eligibility_result_selector_module.EligibilityResultSelector,
            "get_by_id",
            MagicMock(return_value=eligibility_result),
        )

        empty_logs = MagicMock()
        empty_logs.exists.return_value = False
        monkeypatch.setattr(
            ai_reasoning_log_selector_module.AIReasoningLogSelector,
            "get_by_case",
            MagicMock(return_value=empty_logs),
        )

        resp = api_client.get(f"{BASE}/cases/{case.id}/eligibility/{result_id}/explanation/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["result_id"] == str(result_id)
        assert "rule_evaluation_details" in resp.data["data"]

    def test_explanation_other_user_forbidden(self, monkeypatch, api_client, other_user, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=other_user)

        result_id = uuid.uuid4()
        eligibility_result = MagicMock()
        eligibility_result.id = result_id
        eligibility_result.case = case
        eligibility_result.rule_version = None
        eligibility_result.reasoning_summary = "ok"

        from ai_decisions.selectors import eligibility_result_selector as eligibility_result_selector_module

        monkeypatch.setattr(
            eligibility_result_selector_module.EligibilityResultSelector,
            "get_by_id",
            MagicMock(return_value=eligibility_result),
        )

        resp = api_client.get(f"{BASE}/cases/{case.id}/eligibility/{result_id}/explanation/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_explanation_result_not_found_returns_404(self, monkeypatch, api_client, case_owner, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)

        from ai_decisions.selectors import eligibility_result_selector as eligibility_result_selector_module

        monkeypatch.setattr(
            eligibility_result_selector_module.EligibilityResultSelector,
            "get_by_id",
            MagicMock(return_value=None),
        )

        resp = api_client.get(f"{BASE}/cases/{case.id}/eligibility/{uuid.uuid4()}/explanation/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_explanation_result_wrong_case_returns_400(self, monkeypatch, api_client, case_owner, paid_case_with_fact):
        case, _fact = paid_case_with_fact
        api_client.force_authenticate(user=case_owner)

        result_id = uuid.uuid4()
        other_case = MagicMock()
        other_case.id = uuid.uuid4()

        eligibility_result = MagicMock()
        eligibility_result.id = result_id
        eligibility_result.case = other_case
        eligibility_result.rule_version = None
        eligibility_result.reasoning_summary = "ok"

        from ai_decisions.selectors import eligibility_result_selector as eligibility_result_selector_module

        monkeypatch.setattr(
            eligibility_result_selector_module.EligibilityResultSelector,
            "get_by_id",
            MagicMock(return_value=eligibility_result),
        )

        resp = api_client.get(f"{BASE}/cases/{case.id}/eligibility/{result_id}/explanation/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


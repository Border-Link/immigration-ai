import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestDecisionOverrideViews:
    def test_create_override_requires_reviewer_role(self, api_client, paid_case, eligibility_result, case_owner):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)

        payload = {
            "case_id": str(case.id),
            "original_result_id": str(eligibility_result.id),
            "overridden_outcome": "eligible",
            "reason": "test",
        }
        resp = api_client.post(f"{API_PREFIX}/decision-overrides/create/", payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_override_success_defaults_reviewer_to_request_user(self, api_client, paid_case, eligibility_result, reviewer_user):
        case, _payment = paid_case
        api_client.force_authenticate(user=reviewer_user)

        payload = {
            "case_id": str(case.id),
            "original_result_id": str(eligibility_result.id),
            "overridden_outcome": "eligible",
            "reason": "test",
        }
        resp = api_client.post(f"{API_PREFIX}/decision-overrides/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["case_id"] == str(case.id)

    def test_create_override_validation_case_result_mismatch(self, api_client, paid_case, eligibility_result, reviewer_user):
        case, _payment = paid_case
        api_client.force_authenticate(user=reviewer_user)

        payload = {
            "case_id": str(uuid.uuid4()),
            "original_result_id": str(eligibility_result.id),
            "overridden_outcome": "eligible",
            "reason": "test",
        }
        resp = api_client.post(f"{API_PREFIX}/decision-overrides/create/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_overrides_success(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/decision-overrides/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_detail_override_404_when_missing(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/decision-overrides/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_latest_override_404_when_missing(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/decision-overrides/latest/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


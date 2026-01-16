import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestAdminDecisionOverrideViews:
    def test_admin_overrides_list_forbidden_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/decision-overrides/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_overrides_list_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/decision-overrides/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_admin_overrides_detail_404(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/decision-overrides/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_overrides_delete_success(self, api_client, admin_user, paid_case, eligibility_result, decision_override_service, reviewer_user):
        case, _payment = paid_case
        override = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="admin delete",
            reviewer_id=str(reviewer_user.id),
        )
        assert override is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/decision-overrides/{override.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_overrides_bulk_delete(self, api_client, admin_user, paid_case, eligibility_result, decision_override_service, reviewer_user):
        case, _payment = paid_case
        o1 = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="bulk1",
            reviewer_id=str(reviewer_user.id),
        )
        o2 = decision_override_service.create_decision_override(
            case_id=str(case.id),
            original_result_id=str(eligibility_result.id),
            overridden_outcome="eligible",
            reason="bulk2",
            reviewer_id=str(reviewer_user.id),
        )
        assert o1 is not None and o2 is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/decision-overrides/bulk-operation/",
            {"decision_override_ids": [str(o1.id), str(o2.id)], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2


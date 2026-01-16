import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestAdminEligibilityResultViews:
    def test_admin_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/eligibility-results/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_forbidden_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/eligibility-results/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_allowed(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/eligibility-results/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_admin_detail(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/eligibility-results/{eligibility_result.id}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_update(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.patch(
            f"{API_PREFIX}/admin/eligibility-results/{eligibility_result.id}/update/",
            {"confidence": 0.6, "outcome": "requires_review"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["outcome"] == "requires_review"

    def test_admin_bulk_update_outcome(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/eligibility-results/bulk-operation/",
            {
                "result_ids": [str(eligibility_result.id)],
                "operation": "update_outcome",
                "outcome": "eligible",
                "confidence": 0.9,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_delete(self, api_client, admin_user, eligibility_result_service, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/eligibility-results/{eligibility_result.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK
        assert eligibility_result_service.get_by_id(str(eligibility_result.id)) is None


    def test_admin_bulk_delete_operation(self, api_client, admin_user, eligibility_result, eligibility_result_service):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/eligibility-results/bulk-operation/",
            {"result_ids": [str(eligibility_result.id)], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert eligibility_result_service.get_by_id(str(eligibility_result.id)) is None

    def test_admin_bulk_invalid_operation_is_reported_not_500(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/eligibility-results/bulk-operation/",
            {"result_ids": [str(eligibility_result.id)], "operation": "not-a-real-op"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "operation" in resp.data

    def test_admin_update_invalid_body(self, api_client, admin_user, eligibility_result):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.patch(
            f"{API_PREFIX}/admin/eligibility-results/{eligibility_result.id}/update/",
            {"confidence": 1.5},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_delete_not_found(self, api_client, admin_user):
        import uuid

        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/eligibility-results/{uuid.uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

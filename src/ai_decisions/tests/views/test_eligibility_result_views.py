import pytest
from rest_framework import status


API_PREFIX = "/api/v1/ai-decisions"


@pytest.mark.django_db
class TestEligibilityResultViews:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_user_scoped_results(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/")
        assert resp.status_code == status.HTTP_200_OK
        assert "items" in resp.data["data"]

    def test_list_with_case_id_owner_allowed(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        case_id = str(eligibility_result.case_id)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/?case_id={case_id}")
        assert resp.status_code == status.HTTP_200_OK

    def test_list_with_case_id_other_user_forbidden(self, api_client, other_user, eligibility_result):
        api_client.force_authenticate(user=other_user)
        case_id = str(eligibility_result.case_id)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/?case_id={case_id}")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_invalid_pagination(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/?page_size=0")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_owner_allowed(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(eligibility_result.id)

    def test_detail_other_user_forbidden(self, api_client, other_user, eligibility_result):
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_detail_not_found(self, api_client, case_owner):
        import uuid

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/eligibility-results/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_owner_allowed(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.patch(
            f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/update/",
            {"confidence": 0.5},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert float(resp.data["data"]["confidence"]) == pytest.approx(0.5)

    def test_update_reviewer_forbidden(self, api_client, reviewer_user, eligibility_result):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.patch(
            f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/update/",
            {"confidence": 0.5},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_invalid_body(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.patch(
            f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/update/",
            {"confidence": 1.5},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_owner_allowed(self, api_client, case_owner, eligibility_result):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.delete(f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_delete_other_user_forbidden(self, api_client, other_user, eligibility_result):
        api_client.force_authenticate(user=other_user)
        resp = api_client.delete(f"{API_PREFIX}/eligibility-results/{eligibility_result.id}/delete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


    def test_update_not_found(self, api_client, case_owner):
        import uuid

        api_client.force_authenticate(user=case_owner)
        resp = api_client.patch(
            f"{API_PREFIX}/eligibility-results/{uuid.uuid4()}/update/",
            {"confidence": 0.5},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, api_client, case_owner):
        import uuid

        api_client.force_authenticate(user=case_owner)
        resp = api_client.delete(f"{API_PREFIX}/eligibility-results/{uuid.uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

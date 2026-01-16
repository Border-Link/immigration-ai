import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestAdminReviewViews:
    def test_admin_list_requires_auth(self, api_client):
        resp = api_client.get(f"{API_PREFIX}/admin/reviews/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_list_forbidden_for_non_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/reviews/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_list_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/reviews/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_admin_detail_404(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/reviews/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_update_success_with_version(self, api_client, admin_user, paid_case, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.put(
            f"{API_PREFIX}/admin/reviews/{review.id}/update/",
            {"status": "cancelled", "version": review.version},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "cancelled"

    def test_admin_update_version_conflict_returns_400(self, api_client, admin_user, paid_case, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.put(
            f"{API_PREFIX}/admin/reviews/{review.id}/update/",
            {"status": "cancelled", "version": review.version + 999},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_delete_success(self, api_client, admin_user, paid_case, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/reviews/{review.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_bulk_operation_delete(self, api_client, admin_user, paid_case, review_service):
        case, _payment = paid_case
        r1 = review_service.create_review(case_id=str(case.id), auto_assign=False)
        r2 = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert r1 is not None and r2 is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/reviews/bulk-operation/",
            {"review_ids": [str(r1.id), str(r2.id)], "operation": "delete"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2


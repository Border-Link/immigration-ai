import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestReviewViews:
    def test_create_review_requires_auth(self, api_client):
        resp = api_client.post(f"{API_PREFIX}/reviews/create/", {}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_review_success(self, api_client, paid_case, case_owner, reviewer_user):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)

        payload = {
            "case_id": str(case.id),
            "reviewer_id": str(reviewer_user.id),
            "auto_assign": False,
            "assignment_strategy": "round_robin",
        }
        resp = api_client.post(f"{API_PREFIX}/reviews/create/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert str(resp.data["data"]["case"]) == str(case.id)

    def test_create_review_invalid_case_id(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        payload = {"case_id": str(uuid.uuid4())}
        resp = api_client.post(f"{API_PREFIX}/reviews/create/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reviews_success(self, api_client, paid_case, case_owner, review_service):
        case, _payment = paid_case
        review_service.create_review(case_id=str(case.id), auto_assign=False)

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_list_reviews_filter_by_case_id(self, api_client, paid_case, case_owner, review_service):
        case, _payment = paid_case
        created = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert created is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/?case_id={case.id}")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(created.id) in ids

    def test_detail_review_404_when_missing(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_review_success(self, api_client, paid_case, case_owner, review_service):
        case, _payment = paid_case
        created = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert created is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/{created.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(created.id)

    def test_pending_reviews_endpoint(self, api_client, paid_case, case_owner, reviewer_user, review_service):
        case, _payment = paid_case
        pending = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assigned = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user.id), auto_assign=False)
        assert pending is not None
        assert assigned is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/pending/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(pending.id) in ids
        assert str(assigned.id) not in ids

    def test_my_reviews_endpoint(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/reviews/my-reviews/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in resp.data["data"]}
        assert str(review.id) in ids

    def test_update_review_success(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.patch(f"{API_PREFIX}/reviews/{review.id}/update/", {"status": "cancelled"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "cancelled"

    def test_update_review_invalid_transition_returns_400(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.patch(f"{API_PREFIX}/reviews/{review.id}/update/", {"status": "completed"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_reviewer_success(self, api_client, paid_case, reviewer_user, review_service, user_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        # Ensure reviewer is valid and staff
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{API_PREFIX}/reviews/{review.id}/assign/",
            {"reviewer_id": str(reviewer_user.id), "assignment_strategy": "round_robin"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "in_progress"

    def test_complete_review_success(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/complete/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "completed"

    def test_complete_review_invalid_transition_returns_404(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/complete/", {}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_review_success(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/cancel/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "cancelled"

    def test_delete_review_success(self, api_client, paid_case, reviewer_user, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.delete(f"{API_PREFIX}/reviews/{review.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_delete_review_missing_returns_404(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.delete(f"{API_PREFIX}/reviews/{uuid.uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


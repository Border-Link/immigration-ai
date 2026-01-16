import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestReviewActionsViews:
    def test_reassign_requires_auth(self, api_client):
        resp = api_client.post(f"{API_PREFIX}/reviews/{uuid.uuid4()}/reassign/", {}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reassign_validation_error(self, api_client, case_owner, paid_case, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/reassign/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reassign_success(self, api_client, paid_case, review_service, reviewer_user, user_service, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), reviewer_id=str(reviewer_user.id), auto_assign=False)
        assert review is not None

        new_reviewer = user_service.create_user(email=f"reviewer3-hr-{uuid.uuid4().hex[:6]}@example.com", password="reviewerpass123")
        user_service.update_user(new_reviewer, role="reviewer", is_staff=True)
        user_service.activate_user(new_reviewer)

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(
            f"{API_PREFIX}/reviews/{review.id}/reassign/",
            {"new_reviewer_id": str(new_reviewer.id), "reason": "workload"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["data"]["reviewer"]) == str(new_reviewer.id)

    def test_escalate_success(self, api_client, paid_case, review_service, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(
            f"{API_PREFIX}/reviews/{review.id}/escalate/",
            {"reason": "complex", "priority": "urgent"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_approve_success(self, api_client, paid_case, review_service, reviewer_user, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/approve/", {"reason": "ok"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "completed"

    def test_reject_requires_reason(self, api_client, paid_case, review_service, reviewer_user, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/reject/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_success_sets_pending(self, api_client, paid_case, review_service, reviewer_user, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/reject/", {"reason": "needs changes"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "pending"

    def test_request_changes_requires_reason(self, api_client, paid_case, review_service, reviewer_user, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{API_PREFIX}/reviews/{review.id}/request-changes/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_request_changes_success(self, api_client, paid_case, review_service, reviewer_user, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None
        assert review.status == "in_progress"

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(
            f"{API_PREFIX}/reviews/{review.id}/request-changes/",
            {"reason": "update docs"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "in_progress"


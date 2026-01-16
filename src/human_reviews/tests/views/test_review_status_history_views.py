import uuid

import pytest
from rest_framework import status

from human_reviews.selectors.review_status_history_selector import ReviewStatusHistorySelector


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestReviewStatusHistoryViews:
    def test_list_history_404_when_review_missing(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/{uuid.uuid4()}/status-history/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_list_history_success(self, api_client, paid_case, reviewer_user, case_owner, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        review = review_service.cancel_review(str(review.id))
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/{review.id}/status-history/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)
        assert len(resp.data["data"]) >= 1

    def test_detail_history_404_when_missing(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/status-history/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_history_success(self, api_client, paid_case, reviewer_user, case_owner, review_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        history = ReviewStatusHistorySelector.get_by_review(review).first()
        assert history is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/status-history/{history.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(history.id)


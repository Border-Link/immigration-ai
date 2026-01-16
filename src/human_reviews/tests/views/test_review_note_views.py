import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestReviewNoteViews:
    def test_create_note_requires_reviewer_role(self, api_client, paid_case, review_service, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        assert review is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(
            f"{API_PREFIX}/review-notes/create/",
            {"review_id": str(review.id), "note": "hello", "is_internal": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_note_success(self, api_client, paid_case, review_service, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{API_PREFIX}/review-notes/create/",
            {"review_id": str(review.id), "note": "hello", "is_internal": False},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["review_id"] == str(review.id)

    def test_create_note_validation_empty_note(self, api_client, paid_case, review_service, reviewer_user):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.post(
            f"{API_PREFIX}/review-notes/create/",
            {"review_id": str(review.id), "note": "   "},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_notes_success(self, api_client, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None
        review_note_service.create_review_note(review_id=str(review.id), note="public", is_internal=False)

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/review-notes/?review_id={review.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)
        assert len(resp.data["data"]) >= 1

    def test_detail_note_404_when_missing(self, api_client, reviewer_user):
        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.get(f"{API_PREFIX}/review-notes/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_public_notes_endpoint_only_returns_public(self, api_client, paid_case, review_service, reviewer_user, review_note_service, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        assert review is not None

        review_note_service.create_review_note(review_id=str(review.id), note="public", is_internal=False)
        review_note_service.create_review_note(review_id=str(review.id), note="internal", is_internal=True)

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/reviews/{review.id}/notes/public/")
        assert resp.status_code == status.HTTP_200_OK
        assert all(item["is_internal"] is False for item in resp.data["data"])

    def test_update_note_requires_reviewer_role(self, api_client, paid_case, review_service, reviewer_user, review_note_service, case_owner):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        note = review_note_service.create_review_note(review_id=str(review.id), note="before", is_internal=False)
        assert note is not None

        api_client.force_authenticate(user=case_owner)
        resp = api_client.patch(f"{API_PREFIX}/review-notes/{note.id}/update/", {"note": "after"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_note_success(self, api_client, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        note = review_note_service.create_review_note(review_id=str(review.id), note="before", is_internal=False)
        assert note is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.patch(f"{API_PREFIX}/review-notes/{note.id}/update/", {"note": "after", "is_internal": True}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["note"] == "after"
        assert resp.data["data"]["is_internal"] is True

    def test_delete_note_success(self, api_client, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        note = review_note_service.create_review_note(review_id=str(review.id), note="to delete", is_internal=False)
        assert note is not None

        api_client.force_authenticate(user=reviewer_user)
        resp = api_client.delete(f"{API_PREFIX}/review-notes/{note.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK


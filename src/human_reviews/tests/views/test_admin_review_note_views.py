import uuid

import pytest
from rest_framework import status


API_PREFIX = "/api/v1/human-reviews"


@pytest.mark.django_db
class TestAdminReviewNoteViews:
    def test_admin_notes_list_requires_staff(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{API_PREFIX}/admin/review-notes/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_notes_list_success(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/review-notes/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.data["data"], list)

    def test_admin_notes_detail_404(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        resp = api_client.get(f"{API_PREFIX}/admin/review-notes/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_notes_update_success(self, api_client, admin_user, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        note = review_note_service.create_review_note(review_id=str(review.id), note="before", is_internal=False)
        assert note is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.put(f"{API_PREFIX}/admin/review-notes/{note.id}/update/", {"is_internal": True}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["is_internal"] is True

    def test_admin_notes_delete_success(self, api_client, admin_user, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        note = review_note_service.create_review_note(review_id=str(review.id), note="to delete", is_internal=False)
        assert note is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.delete(f"{API_PREFIX}/admin/review-notes/{note.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_notes_bulk_set_internal(self, api_client, admin_user, paid_case, review_service, reviewer_user, review_note_service):
        case, _payment = paid_case
        review = review_service.create_review(case_id=str(case.id), auto_assign=False)
        review = review_service.assign_reviewer(str(review.id), reviewer_id=str(reviewer_user.id))
        n1 = review_note_service.create_review_note(review_id=str(review.id), note="n1", is_internal=False)
        n2 = review_note_service.create_review_note(review_id=str(review.id), note="n2", is_internal=False)
        assert n1 is not None and n2 is not None

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(
            f"{API_PREFIX}/admin/review-notes/bulk-operation/",
            {"review_note_ids": [str(n1.id), str(n2.id)], "operation": "set_internal"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) >= 2


"""
API tests for public call session endpoints in `ai_calls`.
"""

import pytest
from rest_framework import status
from unittest.mock import MagicMock


BASE = "/api/v1/ai-calls"


@pytest.mark.django_db
class TestCallSessionCreateAPI:
    def test_create_requires_auth(self, api_client, paid_case):
        case, _payment = paid_case
        resp = api_client.post(f"{BASE}/sessions/", {"case_id": str(case.id)}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_success(self, api_client, paid_case, case_owner):
        case, _payment = paid_case
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/", {"case_id": str(case.id)}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["status"] == "created"

    def test_create_invalid_case_id_fails(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/", {"case_id": "00000000-0000-0000-0000-000000000000"}, format="json")
        assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

    def test_create_case_not_owned_fails(self, api_client, paid_case, other_user):
        case, _payment = paid_case
        api_client.force_authenticate(user=other_user)
        resp = api_client.post(f"{BASE}/sessions/", {"case_id": str(case.id)}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCallSessionDetailAPI:
    def test_get_requires_auth(self, api_client, call_session_created):
        resp = api_client.get(f"{BASE}/sessions/{call_session_created.id}/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success_for_owner(self, api_client, call_session_created, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/sessions/{call_session_created.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(call_session_created.id)
        assert "time_remaining_seconds" in resp.data["data"]

    def test_get_forbidden_for_other_user(self, api_client, call_session_created, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"{BASE}/sessions/{call_session_created.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/sessions/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCallSessionPrepareStartEndTerminateHeartbeat:
    def test_prepare_success(self, api_client, call_session_created, case_owner, monkeypatch, minimal_context_bundle):
        from ai_calls.services import case_context_builder as case_context_builder_module
        api_client.force_authenticate(user=case_owner)

        monkeypatch.setattr(
            case_context_builder_module.CaseContextBuilder,
            "build_context_bundle",
            MagicMock(return_value=minimal_context_bundle),
        )
        resp = api_client.post(f"{BASE}/sessions/{call_session_created.id}/prepare/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "ready"

    def test_start_success(self, api_client, call_session_ready, case_owner, monkeypatch):
        from ai_calls.services import timebox_service as timebox_service_module
        api_client.force_authenticate(user=case_owner)

        monkeypatch.setattr(
            timebox_service_module.TimeboxService,
            "schedule_timebox_enforcement",
            MagicMock(return_value="task1"),
        )
        resp = api_client.post(f"{BASE}/sessions/{call_session_ready.id}/start/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "in_progress"

    def test_end_success(self, api_client, call_session_in_progress, case_owner, monkeypatch):
        from ai_calls.services import post_call_summary_service as summary_module
        api_client.force_authenticate(user=case_owner)

        monkeypatch.setattr(summary_module.PostCallSummaryService, "generate_summary", MagicMock(return_value=None))
        monkeypatch.setattr(summary_module.PostCallSummaryService, "attach_to_case_timeline", MagicMock(return_value=True))

        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/end/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "completed"

    def test_terminate_requires_reason(self, api_client, call_session_in_progress, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/terminate/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_terminate_success(self, api_client, call_session_in_progress, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/terminate/", {"reason": "done"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "terminated"

    def test_heartbeat_success(self, api_client, call_session_in_progress, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.post(f"{BASE}/sessions/{call_session_in_progress.id}/heartbeat/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "in_progress"


@pytest.mark.django_db
class TestCallSessionTranscriptAPI:
    def test_transcript_empty(self, api_client, call_session_in_progress, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/sessions/{call_session_in_progress.id}/transcript/")
        assert resp.status_code == status.HTTP_200_OK
        assert "turns" in resp.data["data"]
        assert resp.data["data"]["total_turns"] == 0

    def test_transcript_not_found(self, api_client, case_owner):
        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/sessions/00000000-0000-0000-0000-000000000000/transcript/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_transcript_forbidden_for_other_user(self, api_client, call_session_in_progress, other_user):
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"{BASE}/sessions/{call_session_in_progress.id}/transcript/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_transcript_with_turns(self, api_client, call_session_in_progress, case_owner):
        from ai_calls.repositories.call_transcript_repository import CallTranscriptRepository

        CallTranscriptRepository.create_transcript_turn(
            call_session=call_session_in_progress, turn_type="user", text="Hello?", speech_confidence=0.9
        )
        CallTranscriptRepository.create_transcript_turn(
            call_session=call_session_in_progress, turn_type="ai", text="Based on your case information, hi.", ai_model="test-model"
        )

        api_client.force_authenticate(user=case_owner)
        resp = api_client.get(f"{BASE}/sessions/{call_session_in_progress.id}/transcript/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["total_turns"] == 2
        assert len(resp.data["data"]["turns"]) == 2

"""
Tests for CaseStatusHistoryService.
"""

import pytest


@pytest.mark.django_db
class TestCaseStatusHistoryService:
    def test_get_by_case_id_returns_history_after_status_change(
        self,
        case_service,
        case_status_history_service,
        paid_case_with_fact,
    ):
        case, _fact = paid_case_with_fact
        current = case_service.get_by_id(str(case.id))

        updated, error, http_status = case_service.update_case(
            case_id=str(case.id),
            version=current.version,
            status="evaluated",
            reason="evaluate",
        )
        assert updated is not None
        assert error is None
        assert http_status is None

        history = case_status_history_service.get_by_case_id(str(case.id))
        assert history.count() >= 1

    def test_get_by_id_not_found_returns_none(self, case_status_history_service):
        assert case_status_history_service.get_by_id("00000000-0000-0000-0000-000000000000") is None


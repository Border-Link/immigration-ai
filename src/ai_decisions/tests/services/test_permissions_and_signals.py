from rest_framework.test import APIRequestFactory
import pytest

from ai_decisions.permissions.eligibility_result_permissions import (
    CanViewEligibilityResult,
    CanModifyEligibilityResult,
)
from ai_decisions.permissions.ai_reasoning_log_permissions import CanViewAIReasoningLog
from ai_decisions.permissions.ai_citation_permissions import CanViewAICitation


@pytest.mark.django_db
class TestAIDecisionsPermissions:
    def test_can_view_eligibility_result_object_permission(
        self,
        eligibility_result,
        case_owner,
        other_user,
        admin_user,
    ):
        factory = APIRequestFactory()
        request = factory.get("/fake")

        perm = CanViewEligibilityResult()

        request.user = case_owner
        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, eligibility_result) is True

        request.user = other_user
        assert perm.has_object_permission(request, None, eligibility_result) is False

        request.user = admin_user
        assert perm.has_object_permission(request, None, eligibility_result) is True

    def test_can_modify_eligibility_result_object_permission(
        self,
        eligibility_result,
        case_owner,
        other_user,
        admin_user,
    ):
        factory = APIRequestFactory()
        request = factory.patch("/fake")

        perm = CanModifyEligibilityResult()

        request.user = case_owner
        assert perm.has_object_permission(request, None, eligibility_result) is True

        request.user = other_user
        assert perm.has_object_permission(request, None, eligibility_result) is False

        request.user = admin_user
        assert perm.has_object_permission(request, None, eligibility_result) is True

    def test_can_view_ai_reasoning_log_permission(self, case_owner, reviewer_user, admin_user):
        factory = APIRequestFactory()
        request = factory.get("/fake")

        perm = CanViewAIReasoningLog()

        request.user = case_owner
        assert perm.has_permission(request, None) is False

        request.user = reviewer_user
        assert perm.has_permission(request, None) is True

        request.user = admin_user
        assert perm.has_permission(request, None) is True

    def test_can_view_ai_citation_permission(self, case_owner, reviewer_user, admin_user):
        factory = APIRequestFactory()
        request = factory.get("/fake")

        perm = CanViewAICitation()

        request.user = case_owner
        assert perm.has_permission(request, None) is False

        request.user = reviewer_user
        assert perm.has_permission(request, None) is True

        request.user = admin_user
        assert perm.has_permission(request, None) is True


@pytest.mark.django_db
class TestEligibilityResultSignals:
    def test_signal_sends_notification_and_email_and_maybe_review(
        self,
        eligibility_result_service,
        paid_case,
        visa_type,
        rule_version,
        monkeypatch,
    ):
        from users_access.services import notification_service as notification_service_module
        from users_access.tasks import email_tasks as email_tasks_module
        from human_reviews.services import review_service as review_service_module

        case, _payment = paid_case

        # This test should validate the eligibility-result signal specifically, so reset
        # mocks that may have been invoked by unrelated setup (payments, rule publishing, etc.).
        notification_service_module.NotificationService.create_notification.reset_mock()
        email_tasks_module.send_eligibility_result_email_task.delay.reset_mock()
        review_service_module.ReviewService.create_review.reset_mock()

        created = eligibility_result_service.create_eligibility_result(
            case_id=str(case.id),
            visa_type_id=str(visa_type.id),
            rule_version_id=str(rule_version.id),
            outcome="eligible",
            confidence=0.55,  # low confidence -> should auto-escalate
            reasoning_summary="test",
        )
        assert created is not None

        assert notification_service_module.NotificationService.create_notification.call_count == 1
        assert email_tasks_module.send_eligibility_result_email_task.delay.call_count == 1
        assert review_service_module.ReviewService.create_review.call_count == 1

    def test_signal_does_not_create_review_for_high_confidence(
        self,
        eligibility_result_service,
        paid_case,
        visa_type,
        rule_version,
    ):
        from human_reviews.services import review_service as review_service_module

        case, _payment = paid_case
        review_service_module.ReviewService.create_review.reset_mock()
        created = eligibility_result_service.create_eligibility_result(
            case_id=str(case.id),
            visa_type_id=str(visa_type.id),
            rule_version_id=str(rule_version.id),
            outcome="eligible",
            confidence=0.95,
            reasoning_summary="test",
        )
        assert created is not None
        assert review_service_module.ReviewService.create_review.call_count == 0


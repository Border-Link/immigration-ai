import uuid

import pytest


@pytest.mark.django_db
class TestEligibilityResultService:
    def test_create_eligibility_result_requires_payment(
        self,
        eligibility_result_service,
        case_without_completed_payment,
        visa_type,
        rule_version,
    ):
        case = case_without_completed_payment
        created = eligibility_result_service.create_eligibility_result(
            case_id=str(case.id),
            visa_type_id=str(visa_type.id),
            rule_version_id=str(rule_version.id),
            outcome="eligible",
            confidence=0.9,
        )
        assert created is None

    def test_create_and_get_by_id(self, eligibility_result_service, eligibility_result):
        fetched = eligibility_result_service.get_by_id(str(eligibility_result.id))
        assert fetched is not None
        assert str(fetched.id) == str(eligibility_result.id)

    def test_get_by_id_not_found(self, eligibility_result_service):
        assert eligibility_result_service.get_by_id(str(uuid.uuid4())) is None

    def test_get_by_case(self, eligibility_result_service, eligibility_result, paid_case):
        case, _payment = paid_case
        results = eligibility_result_service.get_by_case(str(case.id))
        assert results.count() >= 1

    def test_get_by_filters(self, eligibility_result_service, eligibility_result, visa_type):
        # Filter by visa_type and outcome
        results = eligibility_result_service.get_by_filters(
            visa_type_id=str(visa_type.id),
            outcome="eligible",
            min_confidence=0.5,
        )
        assert results.count() >= 1

    def test_get_by_user_access_regular_user_filters_to_own_cases(
        self,
        eligibility_result_service,
        eligibility_result,
        case_owner,
        other_user,
    ):
        owner_results = eligibility_result_service.get_by_user_access(case_owner)
        assert owner_results.filter(id=eligibility_result.id).exists()

        other_results = eligibility_result_service.get_by_user_access(other_user)
        assert not other_results.filter(id=eligibility_result.id).exists()

    def test_get_by_user_access_admin_sees_all(self, eligibility_result_service, eligibility_result, admin_user):
        results = eligibility_result_service.get_by_user_access(admin_user)
        assert results.filter(id=eligibility_result.id).exists()

    def test_get_by_case_with_access_check_denied(
        self,
        eligibility_result_service,
        paid_case,
        other_user,
    ):
        case, _payment = paid_case
        results, error = eligibility_result_service.get_by_case_with_access_check(str(case.id), other_user)
        assert results is None
        assert error is not None

    def test_update_eligibility_result_requires_payment(
        self,
        eligibility_result_service,
        eligibility_result,
        payment_service,
        case_owner,
    ):
        # Soft-delete the attached payment to force PaymentValidator to fail.
        case = eligibility_result.case
        payment = payment_service.get_by_case(str(case.id)).first()
        assert payment is not None
        payment_service.delete_payment(
            payment_id=str(payment.id),
            changed_by=case_owner,
            reason="test delete payment",
            hard_delete=False,
        )
        from payments.helpers.payment_validator import PaymentValidator

        PaymentValidator.invalidate_payment_cache(str(case.id))

        updated = eligibility_result_service.update_eligibility_result(str(eligibility_result.id), confidence=0.1)
        assert updated is None

    def test_delete_eligibility_result_requires_payment(
        self,
        eligibility_result_service,
        eligibility_result,
        payment_service,
        case_owner,
    ):
        case = eligibility_result.case
        payment = payment_service.get_by_case(str(case.id)).first()
        assert payment is not None
        payment_service.delete_payment(
            payment_id=str(payment.id),
            changed_by=case_owner,
            reason="test delete payment",
            hard_delete=False,
        )
        from payments.helpers.payment_validator import PaymentValidator

        PaymentValidator.invalidate_payment_cache(str(case.id))

        assert eligibility_result_service.delete_eligibility_result(str(eligibility_result.id)) is False

    def test_get_statistics_returns_dict(self, eligibility_result_service, eligibility_result):
        stats = eligibility_result_service.get_statistics()
        assert isinstance(stats, dict)


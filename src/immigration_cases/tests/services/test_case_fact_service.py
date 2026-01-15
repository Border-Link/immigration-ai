"""
Tests for CaseFactService.

All tests use services as the entrypoint (no direct model usage in tests).
"""

from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestCaseFactService:
    def test_create_case_fact_invalid_case_returns_none(self, case_fact_service):
        fact = case_fact_service.create_case_fact(
            case_id="00000000-0000-0000-0000-000000000000",
            fact_key="age",
            fact_value=30,
            source="user",
        )
        assert fact is None

    def test_create_case_fact_requires_payment(self, case_fact_service, case_without_completed_payment):
        with pytest.raises(ValidationError) as exc:
            case_fact_service.create_case_fact(
                case_id=str(case_without_completed_payment.id),
                fact_key="age",
                fact_value=30,
                source="user",
            )
        assert "completed payment" in str(exc.value).lower()

    def test_create_case_fact_validates_fact_value(self, case_fact_service, paid_case):
        case, _payment = paid_case
        with pytest.raises(ValidationError) as exc:
            case_fact_service.create_case_fact(
                case_id=str(case.id),
                fact_key="age",
                fact_value=None,
                source="user",
            )
        assert "cannot be none" in str(exc.value).lower()

    def test_create_case_fact_validates_fact_value_type(self, case_fact_service, paid_case):
        case, _payment = paid_case
        with pytest.raises(ValidationError) as exc:
            case_fact_service.create_case_fact(
                case_id=str(case.id),
                fact_key="age",
                fact_value="30",
                source="user",
            )
        assert "must be of type" in str(exc.value).lower()

    def test_create_case_fact_validates_fact_value_range(self, case_fact_service, paid_case):
        case, _payment = paid_case
        with pytest.raises(ValidationError) as exc:
            case_fact_service.create_case_fact(
                case_id=str(case.id),
                fact_key="age",
                fact_value=200,
                source="user",
            )
        assert "between 0 and 150" in str(exc.value).lower()

    def test_create_case_fact_validates_salary_non_negative(self, case_fact_service, paid_case):
        case, _payment = paid_case
        with pytest.raises(ValidationError) as exc:
            case_fact_service.create_case_fact(
                case_id=str(case.id),
                fact_key="salary",
                fact_value=-1,
                source="user",
            )
        assert "cannot be negative" in str(exc.value).lower()

    def test_create_case_fact_success(self, case_fact_service, paid_case):
        case, _payment = paid_case
        fact = case_fact_service.create_case_fact(
            case_id=str(case.id),
            fact_key="age",
            fact_value=30,
            source="user",
        )
        assert fact is not None
        assert str(fact.case.id) == str(case.id)
        assert fact.fact_key == "age"
        assert fact.fact_value == 30
        assert fact.source == "user"

    def test_get_all_and_get_by_case(self, case_fact_service, paid_case_with_fact):
        case, fact = paid_case_with_fact
        all_facts = case_fact_service.get_all()
        assert all_facts.filter(id=fact.id).exists()

        by_case = case_fact_service.get_by_case(str(case.id))
        assert by_case.filter(id=fact.id).exists()

    def test_get_by_id_not_found_returns_none(self, case_fact_service):
        assert case_fact_service.get_by_id("00000000-0000-0000-0000-000000000000") is None

    def test_update_case_fact_not_found_returns_none(self, case_fact_service):
        assert case_fact_service.update_case_fact("00000000-0000-0000-0000-000000000000", fact_value=31) is None

    def test_update_case_fact_payment_block_returns_none(self, monkeypatch, case_fact_service, paid_case_with_fact):
        _case, fact = paid_case_with_fact

        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            MagicMock(return_value=(False, "payment required")),
        )

        updated = case_fact_service.update_case_fact(str(fact.id), fact_value=31)
        assert updated is None

    def test_delete_case_fact_not_found_returns_false(self, case_fact_service):
        assert case_fact_service.delete_case_fact("00000000-0000-0000-0000-000000000000") is False

    def test_delete_case_fact_payment_block_returns_false(self, monkeypatch, case_fact_service, paid_case_with_fact):
        _case, fact = paid_case_with_fact

        from payments.helpers import payment_validator as payment_validator_module

        monkeypatch.setattr(
            payment_validator_module.PaymentValidator,
            "validate_case_has_payment",
            MagicMock(return_value=(False, "payment required")),
        )

        assert case_fact_service.delete_case_fact(str(fact.id)) is False


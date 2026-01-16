from decimal import Decimal
from uuid import uuid4

import pytest

from payments.serializers.payment.create import PaymentCreateSerializer
from payments.serializers.payment.refund import PaymentRefundSerializer
from payments.serializers.payment.admin import BulkPaymentOperationSerializer


@pytest.mark.django_db
class TestPaymentSerializers:
    def test_payment_create_requires_exactly_one_of_case_or_user(self, paid_case, payment_owner):
        case, _attached_payment = paid_case
        s = PaymentCreateSerializer(
            data={"amount": "10.00", "currency": "USD", "payment_provider": "stripe"}
        )
        assert s.is_valid() is False
        assert "non_field_errors" in s.errors

        s2 = PaymentCreateSerializer(
            data={
                "case_id": str(case.id),
                "user_id": str(payment_owner.id),
                "amount": "10.00",
                "currency": "USD",
                "payment_provider": "stripe",
            }
        )
        assert s2.is_valid() is False
        assert "non_field_errors" in s2.errors

    def test_payment_create_amount_limits_enforced(self, payment_owner):
        s = PaymentCreateSerializer(
            data={
                "user_id": str(payment_owner.id),
                "amount": "0.00",
                "currency": "USD",
                "payment_provider": "stripe",
                "plan": "basic",
            }
        )
        assert s.is_valid() is False

        s2 = PaymentCreateSerializer(
            data={
                "user_id": str(payment_owner.id),
                "amount": "1000000.00",
                "currency": "USD",
                "payment_provider": "stripe",
                "plan": "basic",
            }
        )
        assert s2.is_valid() is False
        assert "amount" in s2.errors

    def test_refund_serializer_allows_optional_amount_and_reason(self):
        s = PaymentRefundSerializer(data={})
        assert s.is_valid() is True

        s2 = PaymentRefundSerializer(data={"amount": "10.00", "reason": "duplicate"})
        assert s2.is_valid() is True

    def test_bulk_operation_requires_status_for_update_status(self):
        s = BulkPaymentOperationSerializer(data={"payment_ids": [str(uuid4())], "operation": "update_status"})
        assert s.is_valid() is False
        assert "status" in s.errors


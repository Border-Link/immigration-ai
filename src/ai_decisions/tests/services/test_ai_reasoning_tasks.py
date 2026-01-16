import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task


@pytest.mark.django_db
class TestAIReasoningTasks:
    def test_invalid_case_id_format(self):
        out = run_eligibility_check_task.run(case_id="not-a-uuid", visa_type_id=None)
        assert out["success"] is False
        assert "Invalid case_id format" in out["error"]

    def test_invalid_visa_type_id_format(self):
        out = run_eligibility_check_task.run(case_id=str(uuid.uuid4()), visa_type_id="not-a-uuid")
        assert out["success"] is False
        assert "Invalid visa_type_id format" in out["error"]

    def test_case_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.CaseSelector.get_by_id",
            MagicMock(return_value=None),
        )
        out = run_eligibility_check_task.run(case_id=str(uuid.uuid4()), visa_type_id=None)
        assert out["success"] is False
        assert "not found" in out["error"].lower()

    def test_payment_blocked(self, monkeypatch):
        fake_case = SimpleNamespace(id=str(uuid.uuid4()), jurisdiction="US")
        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.CaseSelector.get_by_id",
            MagicMock(return_value=fake_case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(False, "payment required")),
        )
        out = run_eligibility_check_task.run(case_id=str(fake_case.id), visa_type_id=None)
        assert out["success"] is False
        assert out.get("blocked") is True

    def test_single_visa_type_success(self, monkeypatch):
        case_id = str(uuid.uuid4())
        fake_case = SimpleNamespace(id=case_id, jurisdiction="US")
        visa_type_id = str(uuid.uuid4())
        fake_visa_type = SimpleNamespace(id=visa_type_id, code="US_TEST", name="Test Visa")

        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.CaseSelector.get_by_id",
            MagicMock(return_value=fake_case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )
        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.VisaTypeSelector.get_by_id",
            MagicMock(return_value=fake_visa_type),
        )

        fake_result = SimpleNamespace(
            success=True,
            outcome="likely",
            confidence=0.9,
            requires_human_review=False,
            conflict_detected=False,
            to_dict=lambda: {"success": True, "outcome": "likely", "confidence": 0.9, "requires_human_review": False},
        )
        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.EligibilityCheckService.run_eligibility_check",
            MagicMock(return_value=fake_result),
        )

        out = run_eligibility_check_task.run(case_id=case_id, visa_type_id=visa_type_id)
        assert out["success"] is True
        assert out["outcome"] == "likely"

    def test_multi_visa_type_success(self, monkeypatch):
        case_id = str(uuid.uuid4())
        fake_case = SimpleNamespace(id=case_id, jurisdiction="US")

        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.CaseSelector.get_by_id",
            MagicMock(return_value=fake_case),
        )
        monkeypatch.setattr(
            "payments.helpers.payment_validator.PaymentValidator.validate_case_has_payment",
            MagicMock(return_value=(True, None)),
        )

        vt1 = SimpleNamespace(id=str(uuid.uuid4()), code="US_A", name="Visa A")
        vt2 = SimpleNamespace(id=str(uuid.uuid4()), code="US_B", name="Visa B")

        class FakeQS(list):
            def exists(self):
                return len(self) > 0

        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.VisaTypeSelector.get_by_jurisdiction",
            MagicMock(return_value=FakeQS([vt1, vt2])),
        )
        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.CaseService.update_case",
            MagicMock(return_value=(None, None, None)),
        )

        def _fake_run(case_id, visa_type_id, evaluation_date=None, enable_ai_reasoning=True):
            return SimpleNamespace(
                success=True,
                outcome="likely",
                confidence=0.9,
                requires_human_review=False,
                conflict_detected=False,
                to_dict=lambda: {
                    "success": True,
                    "case_id": case_id,
                    "visa_type_id": visa_type_id,
                    "outcome": "likely",
                    "confidence": 0.9,
                    "requires_human_review": False,
                    "conflict_detected": False,
                },
            )

        monkeypatch.setattr(
            "ai_decisions.tasks.ai_reasoning_tasks.EligibilityCheckService.run_eligibility_check",
            MagicMock(side_effect=_fake_run),
        )

        out = run_eligibility_check_task.run(case_id=case_id, visa_type_id=None)
        assert out["success"] is True
        assert out["summary"]["successful"] == 2
        assert len(out["results"]) == 2


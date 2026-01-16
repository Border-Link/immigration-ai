import pytest


@pytest.mark.django_db
class TestAIReasoningLogService:
    def test_create_and_get_by_id(self, ai_reasoning_log_service, paid_case):
        case, _payment = paid_case
        log = ai_reasoning_log_service.create_reasoning_log(
            case_id=str(case.id),
            prompt="Prompt",
            response="Response",
            model_name="test-model",
            tokens_used=10,
        )
        assert log is not None

        fetched = ai_reasoning_log_service.get_by_id(str(log.id))
        assert fetched is not None
        assert str(fetched.id) == str(log.id)

    def test_get_by_id_not_found(self, ai_reasoning_log_service):
        import uuid

        assert ai_reasoning_log_service.get_by_id(str(uuid.uuid4())) is None

    def test_get_by_case(self, ai_reasoning_log_service, reasoning_log, paid_case):
        case, _payment = paid_case
        logs = ai_reasoning_log_service.get_by_case(str(case.id))
        assert logs.count() >= 1

    def test_get_by_model(self, ai_reasoning_log_service, reasoning_log):
        logs = ai_reasoning_log_service.get_by_model("test-model")
        assert logs.count() >= 1

    def test_update_reasoning_log(self, ai_reasoning_log_service, reasoning_log):
        updated = ai_reasoning_log_service.update_reasoning_log(str(reasoning_log.id), tokens_used=999)
        assert updated is not None
        assert updated.tokens_used == 999

    def test_delete_reasoning_log(self, ai_reasoning_log_service, reasoning_log):
        assert ai_reasoning_log_service.delete_reasoning_log(str(reasoning_log.id)) is True
        assert ai_reasoning_log_service.get_by_id(str(reasoning_log.id)) is None

    def test_get_by_filters(self, ai_reasoning_log_service, reasoning_log, paid_case):
        case, _payment = paid_case
        logs = ai_reasoning_log_service.get_by_filters(case_id=str(case.id), min_tokens=100)
        assert logs.count() >= 1

    def test_get_statistics_returns_dict(self, ai_reasoning_log_service, reasoning_log):
        stats = ai_reasoning_log_service.get_statistics()
        assert isinstance(stats, dict)


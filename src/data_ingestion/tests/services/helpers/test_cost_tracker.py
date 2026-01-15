from decimal import Decimal

from data_ingestion.helpers.cost_tracker import calculate_cost, track_usage


class TestCostTracker:
    def test_calculate_cost_known_model(self):
        cost = calculate_cost("gpt-4", prompt_tokens=1000, completion_tokens=1000)
        assert isinstance(cost, Decimal)
        assert cost > 0

    def test_calculate_cost_unknown_model_uses_default(self):
        cost = calculate_cost("unknown-model", prompt_tokens=1000, completion_tokens=0)
        assert cost > 0

    def test_track_usage_returns_expected_fields(self):
        result = track_usage("gpt-4", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}, document_version_id="dv")
        assert result["tokens_used"] == 15
        assert "estimated_cost" in result


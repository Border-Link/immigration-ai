from unittest.mock import MagicMock

import pytest

from ai_decisions.helpers import metrics as metrics_module


@pytest.mark.django_db
class TestAIDecisionsMetrics:
    def test_safe_create_metric_handles_duplicate(self):
        metric_cls = MagicMock()
        metric_cls.side_effect = ValueError("duplicated")
        assert metrics_module._safe_create_metric(metric_cls, "name", "help") is None

    def test_track_functions_are_noops_when_metrics_unavailable(self, monkeypatch):
        # Force all metric objects to None to validate safe no-op behavior.
        for name in [
            "eligibility_checks_total",
            "eligibility_check_duration_seconds",
            "eligibility_check_confidence",
            "ai_reasoning_calls_total",
            "ai_reasoning_duration_seconds",
            "ai_reasoning_tokens_used",
            "ai_reasoning_cost_usd",
            "vector_search_operations_total",
            "vector_search_duration_seconds",
            "vector_search_results_count",
            "vector_search_similarity_score",
            "embedding_generations_total",
            "embedding_generation_duration_seconds",
            "embedding_dimensions",
            "citations_extracted_total",
            "citations_per_reasoning",
            "eligibility_conflicts_total",
            "auto_escalations_total",
        ]:
            monkeypatch.setattr(metrics_module, name, None, raising=False)

        metrics_module.track_eligibility_check(
            outcome="likely",
            requires_review=False,
            conflict_detected=False,
            duration=0.1,
            confidence=0.9,
        )
        metrics_module.track_ai_reasoning(model="gpt-4", status="success", duration=0.2, tokens_prompt=10, tokens_completion=20, cost_usd=0.01)
        metrics_module.track_vector_search(status="success", duration=0.01, results_count=2, similarity_scores=[0.9, 0.8])
        metrics_module.track_embedding_generation(status="success", duration=0.5, model="text-embedding-ada-002", dimensions=1536)
        metrics_module.track_citations_extracted(source_type="url", count=2)
        metrics_module.track_eligibility_conflict(conflict_type="outcome_mismatch")
        metrics_module.track_auto_escalation(reason="low_confidence")


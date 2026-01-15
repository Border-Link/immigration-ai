import pytest
from django.utils import timezone

from data_ingestion.services.rule_parsing.rule_scorer import RuleScorer


class TestRuleScorer:
    def test_calculate_sla_deadline_returns_future_datetime(self):
        now = timezone.now()
        deadline = RuleScorer.calculate_sla_deadline(0.1)
        assert deadline > now


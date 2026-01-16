"""
Unit tests for immigration_cases.helpers.metrics.

These tests validate that metrics helpers:
- Do not raise when Prometheus metrics are unavailable (None)
- Correctly call the underlying metric objects when present

Note: immigration_cases has an autouse fixture that mocks metrics for most tests.
We override it here to test the real helper implementations.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolate_side_effects():
    """
    Override immigration_cases/tests/conftest.py autouse fixture (same name)
    so metrics helpers are NOT replaced with mocks in this module.
    """
    yield


class _FakeMetric:
    def __init__(self):
        self.labels_calls = []
        self.inc_calls = 0
        self.observe_calls = []
        self.set_calls = []

    def labels(self, **kwargs):
        self.labels_calls.append(kwargs)
        return self

    def inc(self):
        self.inc_calls += 1

    def observe(self, value):
        self.observe_calls.append(value)

    def set(self, value):
        self.set_calls.append(value)


def test_safe_create_metric_returns_none_when_metric_class_is_none():
    from immigration_cases.helpers.metrics import _safe_create_metric

    assert _safe_create_metric(None, "any_name", "desc") is None


def test_safe_create_metric_returns_none_on_duplicate_registration():
    from immigration_cases.helpers.metrics import _safe_create_metric

    class _DupMetric:
        def __init__(self, *args, **kwargs):
            raise ValueError("Duplicated timeseries in CollectorRegistry")

    assert _safe_create_metric(_DupMetric, "m", "d") is None


def test_track_functions_noop_when_metrics_are_none(monkeypatch):
    """
    If Prometheus is not installed (or metrics weren't created), helpers should no-op safely.
    """
    from immigration_cases.helpers import metrics as m

    monkeypatch.setattr(m, "case_creations_total", None)
    monkeypatch.setattr(m, "case_updates_total", None)
    monkeypatch.setattr(m, "case_status_transitions_total", None)
    monkeypatch.setattr(m, "case_status_transition_duration_seconds", None)
    monkeypatch.setattr(m, "case_facts_added_total", None)
    monkeypatch.setattr(m, "case_facts_updated_total", None)
    monkeypatch.setattr(m, "case_facts_per_case", None)
    monkeypatch.setattr(m, "case_version_conflicts_total", None)
    monkeypatch.setattr(m, "case_status_history_entries_total", None)
    monkeypatch.setattr(m, "cases_by_status", None)

    # Should not raise
    m.track_case_creation(jurisdiction="US", status="draft")
    m.track_case_update(operation="general_update")
    m.track_case_status_transition(from_status="draft", to_status="evaluated", duration=0.123)
    m.track_case_fact_added(fact_type="age")
    m.track_case_fact_updated(fact_type="salary")
    m.track_case_facts_count(count=3)
    m.track_case_version_conflict(operation="update")
    m.track_case_status_history(to_status="evaluated")
    m.update_cases_by_status(status="draft", jurisdiction="US", count=10)


def test_track_functions_call_underlying_metric_objects(monkeypatch):
    from immigration_cases.helpers import metrics as m

    creations = _FakeMetric()
    updates = _FakeMetric()
    transitions = _FakeMetric()
    transition_duration = _FakeMetric()
    facts_added = _FakeMetric()
    facts_updated = _FakeMetric()
    facts_per_case = _FakeMetric()
    version_conflicts = _FakeMetric()
    history_entries = _FakeMetric()
    by_status = _FakeMetric()

    monkeypatch.setattr(m, "case_creations_total", creations)
    monkeypatch.setattr(m, "case_updates_total", updates)
    monkeypatch.setattr(m, "case_status_transitions_total", transitions)
    monkeypatch.setattr(m, "case_status_transition_duration_seconds", transition_duration)
    monkeypatch.setattr(m, "case_facts_added_total", facts_added)
    monkeypatch.setattr(m, "case_facts_updated_total", facts_updated)
    monkeypatch.setattr(m, "case_facts_per_case", facts_per_case)
    monkeypatch.setattr(m, "case_version_conflicts_total", version_conflicts)
    monkeypatch.setattr(m, "case_status_history_entries_total", history_entries)
    monkeypatch.setattr(m, "cases_by_status", by_status)

    m.track_case_creation(jurisdiction="US", status="draft")
    assert creations.labels_calls == [{"jurisdiction": "US", "status": "draft"}]
    assert creations.inc_calls == 1

    m.track_case_update(operation="general_update")
    assert updates.labels_calls == [{"operation": "general_update"}]
    assert updates.inc_calls == 1

    m.track_case_status_transition(from_status="draft", to_status="evaluated", duration=0.5)
    assert transitions.labels_calls == [{"from_status": "draft", "to_status": "evaluated"}]
    assert transitions.inc_calls == 1
    assert transition_duration.labels_calls == [{"to_status": "evaluated"}]
    assert transition_duration.observe_calls == [0.5]

    m.track_case_fact_added(fact_type="age")
    assert facts_added.labels_calls == [{"fact_type": "age"}]
    assert facts_added.inc_calls == 1

    m.track_case_fact_updated(fact_type="salary")
    assert facts_updated.labels_calls == [{"fact_type": "salary"}]
    assert facts_updated.inc_calls == 1

    m.track_case_facts_count(count=7)
    assert facts_per_case.observe_calls == [7]

    m.track_case_version_conflict(operation="update")
    assert version_conflicts.labels_calls == [{"operation": "update"}]
    assert version_conflicts.inc_calls == 1

    m.track_case_status_history(to_status="evaluated")
    assert history_entries.labels_calls == [{"to_status": "evaluated"}]
    assert history_entries.inc_calls == 1

    m.update_cases_by_status(status="draft", jurisdiction="US", count=12)
    assert by_status.labels_calls == [{"status": "draft", "jurisdiction": "US"}]
    assert by_status.set_calls == [12]


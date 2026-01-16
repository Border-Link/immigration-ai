"""
Unit tests for ai_calls signals.

We call receiver functions directly to avoid relying on app registry ordering.
"""

from unittest.mock import MagicMock


class TestCallSessionSignals:
    def test_post_save_invalidation_bumps_namespace(self, monkeypatch):
        import ai_calls.signals.call_session_signals as signals_module

        monkeypatch.setattr(signals_module, "bump_namespace", MagicMock())

        signals_module.invalidate_call_session_cache(sender=None, instance=MagicMock())
        signals_module.bump_namespace.assert_called_once_with("call_sessions")

    def test_post_delete_invalidation_bumps_namespace(self, monkeypatch):
        import ai_calls.signals.call_session_signals as signals_module

        monkeypatch.setattr(signals_module, "bump_namespace", MagicMock())

        signals_module.invalidate_call_session_cache_on_delete(sender=None, instance=MagicMock())
        signals_module.bump_namespace.assert_called_once_with("call_sessions")


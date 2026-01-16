"""
Tests for prompt governance helpers.
"""

import pytest


class TestPromptGovernance:
    def test_compute_prompt_hash_is_deterministic_and_sha256_length(self):
        from ai_calls.helpers.prompt_governance import compute_prompt_hash

        h1 = compute_prompt_hash("hello")
        h2 = compute_prompt_hash("hello")
        h3 = compute_prompt_hash("hello!")

        assert h1 == h2
        assert h1 != h3
        assert isinstance(h1, str)
        assert len(h1) == 64

    @pytest.mark.parametrize(
        "guardrails_triggered,admin_requested,expected",
        [
            (False, False, False),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ],
    )
    def test_should_store_full_prompt_policy(self, guardrails_triggered, admin_requested, expected):
        from ai_calls.helpers.prompt_governance import should_store_full_prompt

        assert should_store_full_prompt(guardrails_triggered, admin_requested) is expected


import pytest


@pytest.mark.unit
class TestLLMClientHelpers:
    def test_is_retryable_error_recognizes_retryable_types(self, monkeypatch):
        import data_ingestion.helpers.llm_client as lc

        class DummyRateLimitError(Exception):
            pass

        class DummyAPIConnectionError(Exception):
            pass

        class DummyAPITimeoutError(Exception):
            pass

        class DummyAPIError(Exception):
            def __init__(self, status_code=None):
                super().__init__("api error")
                self.status_code = status_code

        monkeypatch.setattr(lc, "RateLimitError", DummyRateLimitError)
        monkeypatch.setattr(lc, "APIConnectionError", DummyAPIConnectionError)
        monkeypatch.setattr(lc, "APITimeoutError", DummyAPITimeoutError)
        monkeypatch.setattr(lc, "APIError", DummyAPIError)

        assert lc._is_retryable_error(DummyRateLimitError()) is True
        assert lc._is_retryable_error(DummyAPIConnectionError()) is True
        assert lc._is_retryable_error(DummyAPITimeoutError()) is True
        assert lc._is_retryable_error(DummyAPIError(status_code=503)) is True
        assert lc._is_retryable_error(DummyAPIError(status_code=401)) is False
        assert lc._is_retryable_error(Exception("x")) is False

    def test_classify_openai_error_maps_to_domain_exceptions(self, monkeypatch):
        import data_ingestion.helpers.llm_client as lc

        class DummyRateLimitError(Exception):
            pass

        class DummyAPIConnectionError(Exception):
            pass

        class DummyAPITimeoutError(Exception):
            pass

        class DummyAPIError(Exception):
            def __init__(self, status_code=None):
                super().__init__("api error")
                self.status_code = status_code

        monkeypatch.setattr(lc, "RateLimitError", DummyRateLimitError)
        monkeypatch.setattr(lc, "APIConnectionError", DummyAPIConnectionError)
        monkeypatch.setattr(lc, "APITimeoutError", DummyAPITimeoutError)
        monkeypatch.setattr(lc, "APIError", DummyAPIError)

        assert isinstance(lc._classify_openai_error(DummyRateLimitError()), lc.LLMRateLimitError)
        assert isinstance(lc._classify_openai_error(DummyAPITimeoutError()), lc.LLMTimeoutError)
        assert isinstance(lc._classify_openai_error(DummyAPIConnectionError()), lc.LLMServiceUnavailableError)
        assert isinstance(lc._classify_openai_error(DummyAPIError(status_code=401)), lc.LLMAPIKeyError)
        assert isinstance(lc._classify_openai_error(DummyAPIError(status_code=503)), lc.LLMServiceUnavailableError)
        assert isinstance(lc._classify_openai_error(DummyAPIError(status_code=418)), lc.LLMInvalidResponseError)


@pytest.mark.django_db
class TestLLMClientExtractRules:
    def test_init_requires_api_key(self, settings, monkeypatch):
        import data_ingestion.helpers.llm_client as lc

        settings.OPENAI_API_KEY = None
        with pytest.raises(lc.LLMAPIKeyError):
            lc.LLMClient()

    def test_extract_rules_truncates_text_and_records_token_usage(self, settings, monkeypatch):
        import data_ingestion.helpers.llm_client as lc
        import data_ingestion.helpers.rule_parsing_constants as rpc
        import data_ingestion.helpers.prompts as prompts

        settings.OPENAI_API_KEY = "test-key"

        # Avoid instantiating a real OpenAI client
        monkeypatch.setattr(lc, "OpenAI", lambda **kwargs: object())

        captured = {"text_len": None, "model": None, "messages": None}

        def fake_user_prompt(jurisdiction_name, jurisdiction, extracted_text):
            captured["text_len"] = len(extracted_text)
            return "USER_PROMPT"

        monkeypatch.setattr(rpc, "MAX_TEXT_LENGTH", 10)
        monkeypatch.setattr(prompts, "get_rule_extraction_user_prompt", fake_user_prompt)
        monkeypatch.setattr(prompts, "get_rule_extraction_system_message", lambda jurisdiction_name: "SYSTEM")
        monkeypatch.setattr(prompts, "get_jurisdiction_name", lambda jurisdiction: "United Kingdom")

        class FakeRateLimiter:
            def __init__(self):
                self.recorded = []

            def wait_if_needed(self, estimated_tokens=None):
                return 0.0

            def record_usage(self, tokens):
                self.recorded.append(tokens)

        fake_rl = FakeRateLimiter()
        monkeypatch.setattr(lc, "get_rate_limiter", lambda: fake_rl)

        def fake_call(**kwargs):
            captured["model"] = kwargs["model"]
            captured["messages"] = kwargs["messages"]
            return {
                "content": '{"ok":true}',
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
                "model": kwargs["model"],
                "processing_time_ms": 5,
            }

        monkeypatch.setattr(lc, "_call_llm_with_retry", lambda **kwargs: fake_call(**kwargs))

        client = lc.LLMClient(timeout=1.0)
        long_text = "X" * 100
        res = client.extract_rules(long_text, jurisdiction="UK")

        assert res["success"] is True
        assert captured["text_len"] == 10  # truncated
        assert captured["messages"][0]["role"] == "system"
        assert captured["messages"][1]["role"] == "user"
        assert fake_rl.recorded == [3]

    def test_extract_rules_uses_fallback_on_retryable_domain_errors(self, settings, monkeypatch):
        import data_ingestion.helpers.llm_client as lc
        import data_ingestion.helpers.prompts as prompts

        settings.OPENAI_API_KEY = "test-key"
        monkeypatch.setattr(lc, "OpenAI", lambda **kwargs: object())

        monkeypatch.setattr(prompts, "get_rule_extraction_user_prompt", lambda **kwargs: "USER")
        monkeypatch.setattr(prompts, "get_rule_extraction_system_message", lambda *_a, **_k: "SYSTEM")
        monkeypatch.setattr(prompts, "get_jurisdiction_name", lambda jurisdiction: "United Kingdom")

        class FakeRateLimiter:
            def wait_if_needed(self, estimated_tokens=None):
                return 0.0

            def record_usage(self, tokens):
                pass

        monkeypatch.setattr(lc, "get_rate_limiter", lambda: FakeRateLimiter())

        calls = {"models": []}

        def fake_call(**kwargs):
            calls["models"].append(kwargs["model"])
            if len(calls["models"]) == 1:
                raise lc.LLMServiceUnavailableError("boom")
            return {
                "content": '{"ok":true}',
                "usage": {"total_tokens": 1},
                "model": kwargs["model"],
                "processing_time_ms": 5,
            }

        monkeypatch.setattr(lc, "_call_llm_with_retry", lambda **kwargs: fake_call(**kwargs))

        client = lc.LLMClient(timeout=1.0)
        res = client.extract_rules("hello", jurisdiction="UK", model="primary", use_fallback=True)

        assert res["success"] is True
        assert calls["models"] == ["primary", lc.FALLBACK_LLM_MODEL]

    def test_extract_rules_fallback_failure_reraises_original(self, settings, monkeypatch):
        import data_ingestion.helpers.llm_client as lc
        import data_ingestion.helpers.prompts as prompts

        settings.OPENAI_API_KEY = "test-key"
        monkeypatch.setattr(lc, "OpenAI", lambda **kwargs: object())

        monkeypatch.setattr(prompts, "get_rule_extraction_user_prompt", lambda **kwargs: "USER")
        monkeypatch.setattr(prompts, "get_rule_extraction_system_message", lambda *_a, **_k: "SYSTEM")
        monkeypatch.setattr(prompts, "get_jurisdiction_name", lambda jurisdiction: "United Kingdom")
        monkeypatch.setattr(lc, "get_rate_limiter", lambda: type("RL", (), {"wait_if_needed": lambda *_a, **_k: 0.0, "record_usage": lambda *_a, **_k: None})())

        err = lc.LLMTimeoutError("timeout")

        def fake_call(**kwargs):
            # first call triggers fallback path, second call fails too
            raise err if kwargs["model"] != lc.FALLBACK_LLM_MODEL else Exception("fallback also failed")

        monkeypatch.setattr(lc, "_call_llm_with_retry", lambda **kwargs: fake_call(**kwargs))

        client = lc.LLMClient(timeout=1.0)
        with pytest.raises(lc.LLMTimeoutError):
            client.extract_rules("hello", jurisdiction="UK", model="primary", use_fallback=True)

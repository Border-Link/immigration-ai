import pytest

from data_ingestion.helpers.text_processor import validate_text_for_parsing, prepare_text_for_llm


class TestTextProcessor:
    def test_validate_text_for_parsing_too_short(self):
        ok, err = validate_text_for_parsing("short", min_length=20)
        assert ok is False
        assert err

    def test_validate_text_for_parsing_ok(self):
        ok, err = validate_text_for_parsing("a" * 50, min_length=20)
        assert ok is True
        assert err is None

    def test_prepare_text_for_llm_no_pii(self):
        text, meta = prepare_text_for_llm("Hello world", redact_pii=True)
        assert "Hello world" in text
        assert isinstance(meta, dict)


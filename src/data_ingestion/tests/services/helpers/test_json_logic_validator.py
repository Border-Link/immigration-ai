import pytest

from data_ingestion.helpers.json_logic_validator import validate_json_logic


class TestJsonLogicValidator:
    def test_validate_json_logic_valid(self):
        ok, err = validate_json_logic({"==": [1, 1]})
        assert ok is True
        assert err is None

    def test_validate_json_logic_invalid_operator(self):
        ok, err = validate_json_logic({"bad_op": [1, 1]})
        assert ok is False
        assert err is not None

    def test_validate_json_logic_non_dict(self):
        ok, err = validate_json_logic(["not", "dict"])  # type: ignore[arg-type]
        assert ok is False
        assert err is not None


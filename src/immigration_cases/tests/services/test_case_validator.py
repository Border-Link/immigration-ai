"""
Unit tests for immigration_cases.helpers.case_validator.

These tests validate pure business rules (no direct model access).
"""

import pytest


class TestCaseValidator:
    def test_validate_fact_key_requires_non_empty_string(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_key("")
        assert is_valid is False
        assert "non-empty string" in (error or "").lower()

        is_valid2, error2 = CaseValidator.validate_fact_key(None)
        assert is_valid2 is False
        assert "non-empty string" in (error2 or "").lower()

        is_valid3, error3 = CaseValidator.validate_fact_key(123)  # type: ignore[arg-type]
        assert is_valid3 is False
        assert "non-empty string" in (error3 or "").lower()

    def test_validate_fact_key_allows_unknown_keys_for_flexibility(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_key("some_custom_key")
        assert is_valid is True
        assert error is None

    def test_validate_fact_value_none_is_invalid(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_value("age", None)
        assert is_valid is False
        assert "cannot be none" in (error or "").lower()

    def test_validate_fact_value_type_mismatch_is_invalid(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_value("age", "30")
        assert is_valid is False
        assert "must be of type" in (error or "").lower()

    def test_validate_fact_value_age_range(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_value("age", -1)
        assert is_valid is False
        assert "between 0 and 150" in (error or "").lower()

        is_valid2, error2 = CaseValidator.validate_fact_value("age", 151)
        assert is_valid2 is False
        assert "between 0 and 150" in (error2 or "").lower()

        is_valid3, error3 = CaseValidator.validate_fact_value("age", 30)
        assert is_valid3 is True
        assert error3 is None

    def test_validate_fact_value_salary_non_negative(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_value("salary", -10)
        assert is_valid is False
        assert "cannot be negative" in (error or "").lower()

        is_valid2, error2 = CaseValidator.validate_fact_value("salary", 0)
        assert is_valid2 is True
        assert error2 is None

    def test_validate_fact_value_work_experience_range(self):
        from immigration_cases.helpers.case_validator import CaseValidator

        is_valid, error = CaseValidator.validate_fact_value("work_experience_years", -1)
        assert is_valid is False
        assert "between 0 and 100" in (error or "").lower()

        is_valid2, error2 = CaseValidator.validate_fact_value("work_experience_years", 101)
        assert is_valid2 is False
        assert "between 0 and 100" in (error2 or "").lower()

        is_valid3, error3 = CaseValidator.validate_fact_value("work_experience_years", 10)
        assert is_valid3 is True
        assert error3 is None


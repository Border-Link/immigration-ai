"""
Tests for prompt builders and constants.

Goal: ensure helper modules are importable and key prompt builders return strings
containing required context fields.
"""

import pytest

from document_handling import constants
from document_handling.helpers.prompts import (
    build_document_classification_prompt,
    get_classification_system_message,
    build_content_validation_prompt,
    get_content_validation_system_message,
    build_expiry_date_extraction_prompt,
    get_expiry_extraction_system_message,
)


@pytest.mark.django_db
class TestPromptsAndConstants:
    def test_constants_module_loads(self):
        # Minimal sanity for coverage and accidental import regressions
        assert hasattr(constants, "__file__")

    def test_classification_prompt_contains_inputs(self):
        prompt = build_document_classification_prompt(
            ocr_text="OCR TEXT HERE",
            file_name="passport.pdf",
            possible_types=["passport", "visa"],
        )
        assert isinstance(prompt, str)
        assert "OCR TEXT HERE" in prompt
        assert "passport.pdf" in prompt

    def test_classification_system_message(self):
        msg = get_classification_system_message()
        assert isinstance(msg, str)
        assert len(msg) > 10

    def test_content_validation_prompt_contains_inputs(self):
        prompt = build_content_validation_prompt(
            ocr_text="OCR TEXT HERE",
            case_facts={"name": "Alice"},
            document_type_code="passport",
            extracted_metadata={"expiry_date": "2030-01-01"},
        )
        assert isinstance(prompt, str)
        assert "OCR TEXT HERE" in prompt
        assert "Alice" in prompt

    def test_content_validation_system_message(self):
        msg = get_content_validation_system_message()
        assert isinstance(msg, str)
        assert len(msg) > 10

    def test_expiry_extraction_prompt_contains_inputs(self):
        prompt = build_expiry_date_extraction_prompt(
            ocr_text="OCR TEXT HERE",
            document_type_code="passport",
            file_name="passport.pdf",
        )
        assert isinstance(prompt, str)
        assert "OCR TEXT HERE" in prompt
        assert "passport" in prompt

    def test_expiry_extraction_system_message(self):
        msg = get_expiry_extraction_system_message()
        assert isinstance(msg, str)
        assert len(msg) > 10


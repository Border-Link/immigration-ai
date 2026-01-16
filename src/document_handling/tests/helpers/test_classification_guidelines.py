import pytest


@pytest.mark.django_db
class TestClassificationGuidelines:
    def test_get_classification_guidelines_contains_sections(self):
        from document_handling.helpers.classification_guidelines import get_classification_guidelines

        guidelines = get_classification_guidelines()
        assert isinstance(guidelines, str)
        assert "Key Indicators" in guidelines
        assert "Confidence Scoring" in guidelines
        assert "Edge Cases" in guidelines

    def test_get_common_document_indicators_is_nonempty(self):
        from document_handling.helpers.classification_guidelines import get_common_document_indicators

        indicators = get_common_document_indicators()
        assert isinstance(indicators, str)
        assert len(indicators) > 50
        assert "PASSPORT" in indicators or "Passport" in indicators

    def test_get_document_indicators_for_types_handles_empty_and_unknown(self):
        from document_handling.helpers.classification_guidelines import get_document_indicators_for_types

        assert get_document_indicators_for_types([]) == ""
        # Unknown types should be ignored, returning empty string when none match
        assert get_document_indicators_for_types(["not_a_real_type"]) == ""

    def test_get_document_indicators_for_types_returns_subset(self):
        from document_handling.helpers.classification_guidelines import get_document_indicators_for_types

        subset = get_document_indicators_for_types(["passport", "bank_statement"])
        assert isinstance(subset, str)
        # Should include at least one of the indicators blocks
        assert "PASSPORT" in subset or "BANK" in subset

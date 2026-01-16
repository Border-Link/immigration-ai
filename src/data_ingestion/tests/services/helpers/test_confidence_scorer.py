import pytest


@pytest.mark.unit
class TestEnhancedConfidenceScorer:
    def test_compute_confidence_score_caps_at_max(self, monkeypatch):
        """
        Given the current weights/bonuses, the raw weighted score can exceed 1.0.
        Ensure the scorer enforces MAX_CONFIDENCE_SCORE.
        """
        from data_ingestion.helpers import confidence_scorer as cs

        monkeypatch.setattr(cs, "is_standard_requirement_code", lambda code: True)
        monkeypatch.setattr(cs, "get_requirement_code_category", lambda code: "fee")
        monkeypatch.setattr(cs, "validate_json_logic", lambda expr: (True, None))

        rule_data = {
            "requirement_code": "FEE_APPLICATION",
            "description": "Applicant must pay the fee",
            "condition_expression": {">=": [{"var": "application_fee"}, 38700]},
            "source_excerpt": "Applicants must pay the fee of £38700 " + ("x" * 120),
        }
        # 600 chars triggers full text-length bonus; also includes numeric "38700" and excerpt present.
        source_text = ("Applicants must pay the fee of £38700 " + ("y" * 560)).strip()

        # document_quality acts as a multiplier; use >1 to ensure we trigger the MAX_CONFIDENCE_SCORE cap.
        score = cs.compute_confidence_score(rule_data, source_text, jurisdiction="UK", document_quality=10.0)
        assert score == cs.MAX_CONFIDENCE_SCORE

    def test_compute_confidence_score_handles_missing_optional_fields(self, monkeypatch):
        from data_ingestion.helpers import confidence_scorer as cs

        monkeypatch.setattr(cs, "validate_json_logic", lambda expr: (False, "invalid"))
        monkeypatch.setattr(cs, "is_standard_requirement_code", lambda code: False)

        score = cs.compute_confidence_score(rule_data={}, source_text="short")
        assert 0.0 <= score <= cs.MAX_CONFIDENCE_SCORE

    def test_ml_path_falls_back_to_enhanced_scoring(self, monkeypatch):
        from data_ingestion.helpers import confidence_scorer as cs

        # Force deterministic enhancements
        monkeypatch.setattr(cs, "validate_json_logic", lambda expr: (True, None))
        monkeypatch.setattr(cs, "is_standard_requirement_code", lambda code: True)
        monkeypatch.setattr(cs, "get_requirement_code_category", lambda code: "fee")

        rule_data = {
            "requirement_code": "FEE_APPLICATION",
            "description": "Minimum fee required",
            "condition_expression": {">=": [{"var": "application_fee"}, 100]},
            "source_excerpt": "fee 100",
        }
        source_text = "fee 100" + ("a" * 600)

        base = cs.compute_confidence_score(rule_data, source_text, use_ml=False)
        ml = cs.compute_confidence_score(rule_data, source_text, use_ml=True, ml_model=object())
        assert ml == base

from data_ingestion.helpers.requirement_codes import (
    get_requirement_code_category,
    is_standard_requirement_code,
)


class TestRequirementCodes:
    def test_get_requirement_code_category_returns_string(self):
        assert isinstance(get_requirement_code_category("FEE_PAYMENT"), str)

    def test_is_standard_requirement_code(self):
        # Should not throw and should return bool for any string
        assert isinstance(is_standard_requirement_code("FEE_PAYMENT"), bool)
        assert isinstance(is_standard_requirement_code("NON_STANDARD_CODE"), bool)


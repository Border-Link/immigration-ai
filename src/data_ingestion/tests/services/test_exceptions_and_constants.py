from data_ingestion.exceptions.rule_parsing_exceptions import (
    RuleParsingError,
    InsufficientTextError,
    LLMTimeoutError,
)


def test_exceptions_inherit_from_base():
    assert issubclass(InsufficientTextError, RuleParsingError)
    assert issubclass(LLMTimeoutError, RuleParsingError)


def test_constants_module_imports():
    import data_ingestion.constants  # noqa: F401


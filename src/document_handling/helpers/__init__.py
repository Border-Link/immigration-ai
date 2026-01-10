from .prompts import (
    build_document_classification_prompt,
    get_classification_system_message,
    get_system_message,  # Backward compatibility
    build_expiry_date_extraction_prompt,
    get_expiry_extraction_system_message,
    build_content_validation_prompt,
    get_content_validation_system_message,
)
from .document_type_descriptions import (
    get_document_type_description,
    format_document_types_for_prompt,
    DOCUMENT_TYPE_DESCRIPTIONS
)
from .classification_guidelines import (
    get_classification_guidelines,
    get_common_document_indicators,
    get_document_indicators_for_types,
    CLASSIFICATION_GUIDELINES,
    COMMON_DOCUMENT_INDICATORS
)
from .llm_helper import (
    call_llm_for_document_processing,
    parse_llm_json_response,
)

__all__ = [
    'build_document_classification_prompt',
    'get_classification_system_message',
    'get_system_message',  # Backward compatibility
    'build_expiry_date_extraction_prompt',
    'get_expiry_extraction_system_message',
    'build_content_validation_prompt',
    'get_content_validation_system_message',
    'get_document_type_description',
    'format_document_types_for_prompt',
    'DOCUMENT_TYPE_DESCRIPTIONS',
    'get_classification_guidelines',
    'get_common_document_indicators',
    'get_document_indicators_for_types',
    'CLASSIFICATION_GUIDELINES',
    'COMMON_DOCUMENT_INDICATORS',
    'call_llm_for_document_processing',
    'parse_llm_json_response',
]


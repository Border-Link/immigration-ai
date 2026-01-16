"""
Prompt templates for LLM-based rule extraction.

This module contains comprehensive prompt templates used by the RuleParsingService
to extract structured immigration requirements from text using LLM.
"""

from .requirement_codes import (
    STANDARD_REQUIREMENT_CODES,
    SALARY_CODES,
    AGE_CODES,
    EXPERIENCE_CODES,
    SPONSOR_CODES,
    LANGUAGE_CODES,
    FINANCIAL_CODES,
    DOCUMENT_CODES,
    FEE_CODES,
    PROCESSING_TIME_CODES,
)


def get_rule_extraction_system_message(jurisdiction_name: str) -> str:
    """
    Get the system message for rule extraction LLM calls.
    
    Args:
        jurisdiction_name: Full name of the jurisdiction (e.g., "United Kingdom")
        
    Returns:
        Formatted system message string
    """
    # Format requirement code examples for the prompt
    eligibility_examples = ', '.join(
        SALARY_CODES[:3] + AGE_CODES[:2] + EXPERIENCE_CODES[:2] + 
        SPONSOR_CODES[:2] + LANGUAGE_CODES[:2] + FINANCIAL_CODES[:2]
    )
    document_examples = ', '.join(DOCUMENT_CODES[:5])
    fee_examples = ', '.join(FEE_CODES[:5])
    processing_time_examples = ', '.join(PROCESSING_TIME_CODES[:3])
    
    # Use .format() instead of f-string to avoid issues with nested braces
    return """You are an expert immigration rule extraction system specialized in parsing {jurisdiction_name} immigration regulations. Your task is to extract structured, machine-readable eligibility requirements from official immigration rule text.

## CORE PRINCIPLES

1. **EXPLICIT EXTRACTION ONLY**: Extract ONLY requirements that are explicitly stated in the text. Do NOT infer, assume, or add requirements that are not directly mentioned.

2. **ACCURACY OVER COMPLETENESS**: It's better to extract fewer accurate requirements than many incorrect ones. If a requirement is ambiguous or unclear, omit it rather than guess.

3. **PRESERVE EXACT VALUES**: When extracting numeric values (salaries, fees, ages, etc.), use the EXACT values from the text. Do not round or approximate.

4. **JSON LOGIC FORMAT**: All condition expressions MUST be valid JSON Logic expressions that can be evaluated programmatically.

## JSON LOGIC EXPRESSION FORMAT

JSON Logic uses operators as keys and arrays as operands. Here are the essential operators:

### Comparison Operators:
- `{{">=": [{{"var": "salary"}}, 38700]}}` - salary >= 38700
- `{{"<=": [{{"var": "age"}}, 65]}}` - age <= 65
- `{{"==": [{{"var": "has_sponsor"}}, true]}}` - has_sponsor == true
- `{{"!=": [{{"var": "nationality"}}, "UK"]}}` - nationality != "UK"
- `{{">": [{{"var": "years_experience"}}, 5]}}` - years_experience > 5
- `{{"<": [{{"var": "age"}}, 18]}}` - age < 18

### Logical Operators:
- `{{"and": [condition1, condition2]}}` - Both conditions must be true
- `{{"or": [condition1, condition2]}}` - At least one condition must be true
- `{{"!": condition}}` - Negation (NOT condition)

### Variable Access:
- `{{"var": "field_name"}}` - Access a variable/field from case facts
- `{{"var": "field_name", "default": 0}}` - With default value

### Examples:

**Simple Salary Threshold:**
```json
{{">=": [{{"var": "salary"}}, 38700]}}
```
Meaning: salary >= 38700

**Age Range:**
```json
{{"and": [
  {{">=": [{{"var": "age"}}, 18]}},
  {{"<=": [{{"var": "age"}}, 65]}}
]}}
```
Meaning: age >= 18 AND age <= 65

**Complex Condition (Salary OR Sponsor):**
```json
{{"or": [
  {{">=": [{{"var": "salary"}}, 50000]}},
  {{
    "and": [
      {{">=": [{{"var": "salary"}}, 38700]}},
      {{"==": [{{"var": "has_sponsor"}}, true]}}
    ]
  }}
]}}
```
Meaning: salary >= 50000 OR (salary >= 38700 AND has_sponsor == true)

**String Matching:**
```json
{{"==": [{{"var": "visa_type"}}, "SKILLED_WORKER"]}}
```
Meaning: visa_type == "SKILLED_WORKER"

## REQUIREMENT TYPES

Extract different types of requirements:

1. **ELIGIBILITY REQUIREMENTS** (rule_type: "eligibility")
   - Salary thresholds, age limits, qualifications, experience, sponsors, language, funds
   - Common codes: {eligibility_examples}

2. **DOCUMENT REQUIREMENTS** (rule_type: "document")
   - Required documents: passports, certificates, proof of funds, education certificates
   - Common codes: {document_examples}

3. **FEE REQUIREMENTS** (rule_type: "fee")
   - Application fees, processing fees, health surcharge, biometric fees
   - Common codes: {fee_examples}

4. **PROCESSING TIME** (rule_type: "processing_time")
   - Expected processing times, deadlines, turnaround times
   - Common codes: {processing_time_examples}

## REQUIREMENT CODE NAMING

Use UPPERCASE with underscores. Be descriptive:
- MIN_SALARY (not just SALARY)
- AGE_MIN, AGE_MAX (not just AGE)
- YEARS_EXPERIENCE_REQUIRED
- HAS_VALID_SPONSOR
- ENGLISH_LANGUAGE_LEVEL
- FUNDS_REQUIRED

## OUTPUT FORMAT

You MUST output valid JSON (no markdown code blocks, no extra text). The structure is:

```json
{{
  "visa_code": "VISA_TYPE_CODE",
  "requirements": [
    {{
      "requirement_code": "REQUIREMENT_CODE",
      "description": "Human-readable description",
      "condition_expression": {{JSON_LOGIC_EXPRESSION}},
      "source_excerpt": "Exact quote from source text"
    }}
  ]
}}
```

## SPECIAL INSTRUCTIONS

1. **Visa Code**: Extract from text if mentioned (e.g., "Skilled Worker Visa" → "SKILLED_WORKER"). If not mentioned, use "UNKNOWN".

2. **Source Excerpt**: Include the exact sentence or phrase from the text that contains the requirement. This is critical for traceability.

3. **Currency Handling**: Use the currency format appropriate for {jurisdiction_name}. Convert amounts to numeric values in condition expressions (remove currency symbols, commas).

4. **Multiple Requirements**: If a single sentence contains multiple requirements, extract them as separate requirement objects.

5. **Conditional Requirements**: If a requirement depends on another condition, use JSON Logic "and" or "or" operators to express the relationship.

6. **Ambiguous Cases**: If you cannot determine a clear requirement, omit it. Do not create requirements based on assumptions.

7. **Date/Time Handling**: Convert time periods to consistent units (days, weeks, months) in condition expressions.

## ERROR PREVENTION

- Always validate that condition_expression is valid JSON Logic
- Ensure numeric values match the source text exactly
- Do not create nested structures beyond what JSON Logic supports
- Use boolean values (true/false) not strings ("true"/"false")
- Use numeric values for comparisons, not strings

Remember: Your output will be used to automatically evaluate visa eligibility. Accuracy and precision are critical.""".format(
        jurisdiction_name=jurisdiction_name,
        eligibility_examples=eligibility_examples,
        document_examples=document_examples,
        fee_examples=fee_examples,
        processing_time_examples=processing_time_examples
    )


def get_rule_extraction_user_prompt(
    jurisdiction_name: str,
    jurisdiction: str,
    extracted_text: str
) -> str:
    """
    Get the user prompt for rule extraction LLM calls.
    
    Args:
        jurisdiction_name: Full name of the jurisdiction (e.g., "United Kingdom")
        jurisdiction: Jurisdiction code (e.g., "UK", "US", "CA", "AU")
        extracted_text: The text content to extract rules from
        
    Returns:
        Formatted user prompt string
    """
    # Get jurisdiction-specific currency examples
    jurisdiction_examples = {
        'UK': {"currency": "£", "amount": "38,700"},
        'US': {"currency": "$", "amount": "60,000"},
        'CA': {"currency": "CAD $", "amount": "55,000"},
        'AU': {"currency": "AUD $", "amount": "70,000"},
    }
    
    example = jurisdiction_examples.get(jurisdiction, {"currency": "$", "amount": "50,000"})
    example_currency = example["currency"]
    example_amount = example["amount"]
    
    # Use .format() instead of f-string to avoid issues with nested braces
    return """Extract structured eligibility requirements from the following {jurisdiction_name} immigration rule text.

## OUTPUT FORMAT

You must output valid JSON (no markdown, no code blocks, just pure JSON) with this structure:

{{
  "visa_code": "VISA_TYPE_CODE",
  "requirements": [
    {{
      "requirement_code": "REQUIREMENT_CODE",
      "description": "Clear description of the requirement",
      "condition_expression": {{JSON_LOGIC_EXPRESSION}},
      "source_excerpt": "Exact quote from the text"
    }}
  ]
}}

## EXAMPLES

### Example 1: Salary Requirement
If text says: "Applicants must earn at least {example_currency}{example_amount} per year"
Extract as:
{{
  "requirement_code": "MIN_SALARY",
  "description": "Minimum annual salary requirement",
  "condition_expression": {{">=": [{{"var": "salary"}}, 38700]}},
  "source_excerpt": "Applicants must earn at least {example_currency}{example_amount} per year"
}}

### Example 2: Age Requirement
If text says: "Applicants must be between 18 and 65 years old"
Extract as:
{{
  "requirement_code": "AGE_RANGE",
  "description": "Age must be between 18 and 65 years",
  "condition_expression": {{
    "and": [
      {{">=": [{{"var": "age"}}, 18]}},
      {{"<=": [{{"var": "age"}}, 65]}}
    ]
  }},
  "source_excerpt": "Applicants must be between 18 and 65 years old"
}}

### Example 3: Document Requirement
If text says: "A valid passport is required"
Extract as:
{{
  "requirement_code": "DOCUMENT_PASSPORT",
  "description": "Valid passport required",
  "condition_expression": {{"==": [{{"var": "has_passport"}}, true]}},
  "source_excerpt": "A valid passport is required"
}}

### Example 4: Fee Requirement
If text says: "The application fee is {example_currency}{example_amount}"
Extract as:
{{
  "requirement_code": "FEE_APPLICATION",
  "description": "Application fee amount",
  "condition_expression": {{"==": [{{"var": "application_fee"}}, 38700]}},
  "source_excerpt": "The application fee is {example_currency}{example_amount}"
}}

## IMPORTANT REMINDERS

1. Extract ONLY explicitly stated requirements - do not infer
2. Use exact numeric values from the text
3. Ensure condition_expression is valid JSON Logic
4. Include the exact source_excerpt for traceability
5. Use appropriate requirement_code naming (UPPERCASE_WITH_UNDERSCORES)
6. Output pure JSON only - no markdown formatting, no code blocks

## TEXT TO EXTRACT FROM:

{extracted_text}

Now extract the requirements and output the JSON:""".format(
        jurisdiction_name=jurisdiction_name,
        example_currency=example_currency,
        example_amount=example_amount,
        extracted_text=extracted_text
    )


def get_jurisdiction_name(jurisdiction: str) -> str:
    """
    Get the full name of a jurisdiction from its code.
    
    Args:
        jurisdiction: Jurisdiction code (UK, US, CA, AU)
        
    Returns:
        Full jurisdiction name
    """
    jurisdiction_names = {
        'UK': 'United Kingdom',
        'US': 'United States',
        'CA': 'Canada',
        'AU': 'Australia'
    }
    return jurisdiction_names.get(jurisdiction, jurisdiction)

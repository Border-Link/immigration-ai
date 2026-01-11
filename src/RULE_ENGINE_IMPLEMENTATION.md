# Rule Engine Service Implementation

## Overview

The Rule Engine Service has been successfully implemented as a **stateless, scalable, jurisdiction-agnostic** service for evaluating immigration eligibility rules using JSON Logic expressions.

## Design Pattern

The implementation follows a **Service Layer Pattern** with the following characteristics:

1. **Stateless Design**: All methods are static, no instance state
   - Enables horizontal scaling across multiple instances
   - Thread-safe and concurrent-request friendly

2. **Jurisdiction-Agnostic**: Works with any jurisdiction (UK, US, Canada, etc.)
   - Uses rule versioning system to handle different jurisdictions
   - No hardcoded jurisdiction-specific logic
   - Rules are stored in database, not in code

3. **Separation of Concerns**: Clear separation between:
   - Data loading (selectors)
   - Rule evaluation (service)
   - Result aggregation (service)

4. **Error Resilience**: Handles edge cases gracefully:
   - Missing facts
   - Invalid JSON Logic expressions
   - Missing rule versions
   - Multiple active rule versions

## Architecture

```
RuleEngineService (Stateless)
├── load_case_facts()           # Step 1: Load and convert to dict
├── load_active_rule_version()  # Step 2: Get active version by date
├── extract_variables_from_expression()  # Helper: Extract variables
├── evaluate_requirement()      # Step 3: Evaluate single requirement
├── evaluate_all_requirements() # Step 3: Evaluate all requirements
├── aggregate_results()         # Step 4: Compute outcome & confidence
└── run_eligibility_evaluation() # Main orchestration method
```

## Key Features

### 1. Multi-Jurisdiction Support
- Works with UK, US, Canada, and any future jurisdictions
- Jurisdiction is determined by the visa type's jurisdiction field
- Rule versions are jurisdiction-specific through visa types

### 2. Temporal Rule Versioning
- Evaluates rules based on effective dates
- Handles rule changes over time
- Supports historical evaluations (evaluate against past rules)

### 3. JSON Logic Expression Evaluation
- Uses `json-logic-py` library for expression evaluation
- Supports complex conditional logic
- Handles missing variables gracefully

### 4. Structured Results
- Returns `RuleEngineEvaluationResult` object
- Includes detailed requirement-level results
- Tracks missing facts and errors
- Computes confidence scores and outcomes

## Usage Examples

### Basic Usage

```python
from rules_knowledge.services.rule_engine_service import RuleEngineService

# Run complete eligibility evaluation
result = RuleEngineService.run_eligibility_evaluation(
    case_id="550e8400-e29b-41d4-a716-446655440000",
    visa_type_id="660e8400-e29b-41d4-a716-446655440001"
)

if result:
    print(f"Outcome: {result.outcome}")  # likely, possible, or unlikely
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Requirements Passed: {result.requirements_passed}/{result.requirements_total}")
    
    # Convert to dict for API response
    result_dict = result.to_dict()
```

### Step-by-Step Evaluation

```python
# Step 1: Load case facts
case_facts = RuleEngineService.load_case_facts(case_id)

# Step 2: Load active rule version
rule_version = RuleEngineService.load_active_rule_version(visa_type_id)

# Step 3: Evaluate all requirements
evaluation_results = RuleEngineService.evaluate_all_requirements(
    rule_version,
    case_facts
)

# Step 4: Aggregate results
result = RuleEngineService.aggregate_results(evaluation_results, rule_version)
```

### Evaluate Single Requirement

```python
from rules_knowledge.selectors.visa_requirement_selector import VisaRequirementSelector

requirement = VisaRequirementSelector.get_by_id(requirement_id)
case_facts = {"salary": 42000, "age": 29}

result = RuleEngineService.evaluate_requirement(requirement, case_facts)
print(f"Passed: {result['passed']}")
print(f"Missing Facts: {result['missing_facts']}")
```

## Outcome Mapping

The service maps evaluation results to outcomes:

- **likely**: Confidence >= 0.8 AND no missing facts
- **possible**: Confidence >= 0.5
- **unlikely**: Confidence < 0.5 OR missing critical facts

## Confidence Score Calculation

```
Confidence = (Passed Requirements) / (Total Evaluable Requirements)

Where:
- Total Evaluable = Total Requirements - Requirements with Missing Facts
- If no requirements can be evaluated, confidence = 0.0
```

## JSON Logic Expression Examples

The service evaluates JSON Logic expressions stored in `VisaRequirement.condition_expression`:

### Example 1: Salary Threshold
```json
{
  ">=": [
    {"var": "salary"},
    38700
  ]
}
```

### Example 2: Age Range
```json
{
  "and": [
    {">=": [{"var": "age"}, 18]},
    {"<=": [{"var": "age"}, 65]}
  ]
}
```

### Example 3: Complex Condition
```json
{
  "or": [
    {">=": [{"var": "salary"}, 50000]},
    {
      "and": [
        {">=": [{"var": "salary"}, 38700]},
        {"==": [{"var": "has_sponsor"}, true]}
      ]
    }
  ]
}
```

## Error Handling

The service handles various error scenarios:

1. **Missing Case**: Raises `ValueError` if case not found
2. **Missing Visa Type**: Raises `ValueError` if visa type not found
3. **No Active Rule Version**: Returns `None` (logged as warning)
4. **Missing Facts**: Tracks in result, doesn't fail evaluation
5. **Invalid Expressions**: Tracks error in result, continues with other requirements
6. **Multiple Active Versions**: Uses most recent, logs warning

## Scalability Considerations

1. **Stateless**: Can run on multiple servers
2. **Database Queries**: Uses select_related for optimization
3. **Caching**: Can be added at service layer if needed
4. **Async Support**: Can be wrapped in async tasks (Celery)

## Integration Points

The Rule Engine Service integrates with:

1. **Case Facts**: `immigration_cases.selectors.CaseFactSelector`
2. **Rule Versions**: `rules_knowledge.selectors.VisaRuleVersionSelector`
3. **Requirements**: `rules_knowledge.selectors.VisaRequirementSelector`
4. **Visa Types**: `rules_knowledge.selectors.VisaTypeSelector`

## Dependencies

- `json-logic-py~=1.2.0` - Added to requirements.txt
- Django ORM for database queries
- Existing selectors and models

## Testing Recommendations

1. **Unit Tests**: Test each method independently
2. **Integration Tests**: Test full evaluation flow
3. **Edge Cases**: Test missing facts, invalid expressions, multiple versions
4. **Jurisdiction Tests**: Test with UK, US, Canada visa types
5. **Performance Tests**: Test with large number of requirements

## Next Steps

1. ✅ Rule Engine Service implemented
2. ⏳ Integrate with Eligibility Check API endpoint
3. ⏳ Integrate with AI Reasoning Service (for hybrid evaluation)
4. ⏳ Add caching layer (optional, for performance)
5. ⏳ Add comprehensive tests

## Files Created/Modified

1. **Created**: `src/rules_knowledge/services/rule_engine_service.py`
   - Main service implementation
   - `RuleEngineService` class
   - `RuleEngineEvaluationResult` class

2. **Created**: `src/rules_knowledge/services/rule_engine_example.py`
   - Usage examples
   - Documentation examples

3. **Modified**: `src/rules_knowledge/services/__init__.py`
   - Added exports for RuleEngineService

4. **Modified**: `requirements.txt`
   - Added `json-logic-py~=1.2.0`

## Design Decisions

1. **Why Stateless?**
   - Enables horizontal scaling
   - Thread-safe
   - Easier to test and maintain

2. **Why JSON Logic?**
   - Standard format for rule expressions
   - Flexible and expressive
   - Can be stored in database
   - Supports complex conditions

3. **Why Separate Result Class?**
   - Type safety
   - Clear API
   - Easy to extend
   - Can convert to dict for API responses

4. **Why Not Use Selector for Active Rule Version?**
   - Selector uses `get_current_by_visa_type` which takes VisaType object
   - Service needs to accept visa_type_id and evaluation_date
   - Direct query in service is acceptable for this use case

## Performance Considerations

- Uses `select_related` for efficient database queries
- Processes requirements sequentially (can be parallelized if needed)
- No N+1 query problems
- Can be optimized with caching if required

## Security Considerations

- Input validation (case_id, visa_type_id must be valid UUIDs)
- No SQL injection (uses ORM)
- No code injection (JSON Logic is safe)
- Error messages don't expose sensitive data


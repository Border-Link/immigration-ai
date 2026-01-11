# Rule Creation Workflow

## Overview

Rules are created through **two main paths** in the system:

1. **Automated Path (Ingestion)**: External sources → AI Parsing → Human Validation → Publishing
2. **Manual Path (Admin)**: Admin creates rules directly via API

Both paths result in `VisaRuleVersion` and `VisaRequirement` entries that can be evaluated by the Rule Engine.

---

## Path 1: Automated Rule Creation (Ingestion Workflow)

### Step-by-Step Flow

```
1. Data Ingestion (Celery Beat)
   ↓
2. Document Fetching & Change Detection
   ↓
3. AI Rule Parsing (LLM)
   ↓
4. ParsedRule Created (status: 'pending')
   ↓
5. RuleValidationTask Created
   ↓
6. Human Reviewer Validates
   ↓
7. Approval → Auto-Publish
   ↓
8. VisaRuleVersion + VisaRequirement Created
   ↓
9. Previous Version Closed
   ↓
10. Users Notified
```

### Detailed Steps

#### Step 1: Data Ingestion
- **Service**: `IngestionService`
- **Trigger**: Celery Beat (scheduled) or Admin trigger
- **Action**: Fetches documents from configured sources (gov.uk, etc.)
- **Output**: `SourceDocument` and `DocumentVersion` created

#### Step 2: Change Detection
- **Service**: `DocumentDiffService`
- **Action**: Compares content hash with previous version
- **Output**: `DocumentDiff` created if changes detected

#### Step 3: AI Rule Parsing
- **Service**: `RuleParsingService`
- **Action**: Calls LLM to extract structured rules from document text
- **Output**: `ParsedRule` entries created with:
  - `visa_code`: Visa type code
  - `extracted_logic`: JSON Logic expression(s)
  - `description`: Human-readable description
  - `confidence_score`: AI confidence (0.0-1.0)
  - `status`: 'pending'

**Example ParsedRule.extracted_logic**:
```json
{
  "requirements": [
    {
      "requirement_code": "MIN_SALARY",
      "description": "Minimum salary threshold",
      "condition_expression": {">=": [{"var": "salary"}, 38700]},
      "source_excerpt": "Applicants must earn at least £38,700 per year"
    }
  ]
}
```

#### Step 4: Validation Task Creation
- **Service**: `RuleParsingService`
- **Action**: Creates `RuleValidationTask` for each parsed rule
- **Output**: Task assigned to reviewer (round-robin or workload-based)

#### Step 5: Human Validation
- **API**: `POST /api/v1/admin/validation-tasks/{id}/approve`
- **Service**: `RuleValidationTaskService.approve_task()`
- **Action**: Reviewer reviews and approves/rejects
- **Output**: Task status updated to 'approved' or 'rejected'

#### Step 6: Publishing (Auto or Manual)
- **Service**: `RulePublishingService.publish_approved_parsed_rule()`
- **Trigger**: Automatic on approval (if `auto_publish=True`) or manual via API
- **Actions**:
  1. Get or create `VisaType` by code and jurisdiction
  2. Create `VisaRuleVersion` with effective date
  3. Create `VisaRequirement` entries from parsed rule
  4. Close previous `VisaRuleVersion` (set `effective_to`)
  5. Publish rule version (`is_published=True`)
  6. Trigger notifications

**Code Example**:
```python
from rules_knowledge.services.rule_publishing_service import RulePublishingService

# Publish from approved parsed rule
result = RulePublishingService.publish_approved_parsed_rule(
    parsed_rule_id="550e8400-e29b-41d4-a716-446655440000",
    effective_from=timezone.now()
)

# Or publish from validation task
result = RulePublishingService.publish_approved_validation_task(
    validation_task_id="660e8400-e29b-41d4-a716-446655440001"
)
```

---

## Path 2: Manual Rule Creation (Admin)

### Direct API Creation

Admins can create rules directly without going through ingestion:

#### Option A: Create Rule Version + Requirements Separately

**1. Create Rule Version**:
```python
POST /api/v1/admin/visa-rule-versions/create/
{
  "visa_type_id": "550e8400-e29b-41d4-a716-446655440000",
  "effective_from": "2024-01-01T00:00:00Z",
  "source_document_version_id": null,
  "is_published": true
}
```

**2. Create Requirements**:
```python
POST /api/v1/admin/visa-requirements/create/
{
  "rule_version_id": "660e8400-e29b-41d4-a716-446655440001",
  "requirement_code": "MIN_SALARY",
  "rule_type": "eligibility",
  "description": "Minimum salary threshold",
  "condition_expression": {
    ">=": [
      {"var": "salary"},
      38700
    ]
  },
  "is_mandatory": true
}
```

#### Option B: Use Publishing Service (Recommended)

```python
from rules_knowledge.services.rule_publishing_service import RulePublishingService

result = RulePublishingService.create_rule_manually(
    visa_type_id="550e8400-e29b-41d4-a716-446655440000",
    requirement_code="MIN_SALARY",
    rule_type="eligibility",
    description="Minimum salary threshold",
    condition_expression={
        ">=": [
            {"var": "salary"},
            38700
        ]
    },
    effective_from=timezone.now(),
    is_mandatory=True
)
```

---

## Rule Publishing Service Methods

### 1. `publish_approved_parsed_rule()`
**Purpose**: Publish an approved parsed rule to production

**Input**:
- `parsed_rule_id`: UUID of approved parsed rule
- `effective_from`: Optional effective date
- `reviewer_notes`: Optional notes

**Output**:
```python
{
    'success': True,
    'rule_version_id': 'uuid',
    'requirements_created': 3,
    'previous_version_closed': True,
    'effective_from': '2024-01-01T00:00:00Z'
}
```

**Workflow**:
1. Load approved parsed rule
2. Get or create visa type
3. Create rule version
4. Create requirements from parsed rule
5. Close previous version
6. Publish rule version
7. Notify users

### 2. `publish_approved_validation_task()`
**Purpose**: Publish from an approved validation task

**Input**:
- `validation_task_id`: UUID of approved validation task
- `effective_from`: Optional effective date

**Output**: Same as `publish_approved_parsed_rule()`

### 3. `create_rule_manually()`
**Purpose**: Create a rule manually (admin use)

**Input**:
- `visa_type_id`: UUID of visa type
- `requirement_code`: Code for requirement
- `rule_type`: Type of requirement
- `description`: Human-readable description
- `condition_expression`: JSON Logic expression
- `effective_from`: Optional effective date
- `is_mandatory`: Whether mandatory

**Output**:
```python
{
    'success': True,
    'rule_version_id': 'uuid',
    'requirement_id': 'uuid'
}
```

---

## Rule Structure

### ParsedRule → VisaRequirement Mapping

**ParsedRule.extracted_logic** can have different structures:

#### Structure 1: Array of Requirements
```json
{
  "requirements": [
    {
      "requirement_code": "MIN_SALARY",
      "description": "Minimum salary threshold",
      "condition_expression": {">=": [{"var": "salary"}, 38700]},
      "is_mandatory": true
    },
    {
      "requirement_code": "AGE_LIMIT",
      "description": "Age requirement",
      "condition_expression": {">=": [{"var": "age"}, 18]},
      "is_mandatory": true
    }
  ]
}
```

#### Structure 2: Single Requirement
```json
{
  "requirement_code": "MIN_SALARY",
  "description": "Minimum salary threshold",
  "condition_expression": {">=": [{"var": "salary"}, 38700]}
}
```

#### Structure 3: Direct JSON Logic
```json
{
  ">=": [
    {"var": "salary"},
    38700
  ]
}
```

The `RulePublishingService` handles all three structures automatically.

---

## Version Management

### Effective Date Handling

When a new rule version is published:

1. **New Version Created**:
   - `effective_from`: Set to specified date (or now)
   - `effective_to`: NULL (current until superseded)
   - `is_published`: True

2. **Previous Version Closed**:
   - `effective_to`: Set to one day before new version's `effective_from`
   - Ensures no gap and no overlap

**Example**:
```
Previous Version:
  effective_from: 2024-01-01
  effective_to: NULL (current)

New Version Published:
  effective_from: 2024-06-01
  effective_to: NULL (current)

Previous Version Updated:
  effective_from: 2024-01-01
  effective_to: 2024-05-31 (one day before new version)
```

### Multiple Active Versions

If multiple versions are active (edge case), the system:
- Uses most recent version (ordered by `effective_from DESC`)
- Logs warning
- Rule Engine handles this gracefully

---

## Integration Points

### 1. Approval → Publishing Integration

The `RuleValidationTaskService.approve_task()` method can auto-publish:

```python
# Auto-publish on approval (default)
task = RuleValidationTaskService.approve_task(
    task_id="...",
    reviewer_notes="Verified against official source",
    auto_publish=True  # Default
)

# Manual publish later
result = RulePublishingService.publish_approved_validation_task(
    validation_task_id="..."
)
```

### 2. Signals

When a rule version is published (`is_published=True`), the signal `handle_rule_version_published` triggers:
- User notifications (in-app)
- Email notifications
- Only for users with active cases for the affected visa type

### 3. API Endpoints

**Publishing Endpoints** (to be created):
- `POST /api/v1/admin/rules/publish-from-parsed-rule/{parsed_rule_id}/`
- `POST /api/v1/admin/rules/publish-from-task/{task_id}/`
- `POST /api/v1/admin/rules/create-manually/`

---

## Example: Complete Workflow

### Automated Path Example

```python
# 1. Ingestion triggers parsing
parsing_result = RuleParsingService.parse_document_version(document_version)
# Creates ParsedRule with status='pending'

# 2. Validation task created automatically
# Task assigned to reviewer

# 3. Reviewer approves
task = RuleValidationTaskService.approve_task(
    task_id="...",
    reviewer_notes="Verified correct",
    auto_publish=True
)
# Auto-publishes to production

# 4. Rule is now available for evaluation
result = RuleEngineService.run_eligibility_evaluation(
    case_id="...",
    visa_type_id="..."
)
```

### Manual Path Example

```python
# Admin creates rule directly
result = RulePublishingService.create_rule_manually(
    visa_type_id="550e8400-e29b-41d4-a716-446655440000",
    requirement_code="MIN_SALARY",
    rule_type="eligibility",
    description="Minimum salary threshold",
    condition_expression={
        ">=": [{"var": "salary"}, 38700]
    },
    effective_from=timezone.now(),
    is_mandatory=True
)

# Rule is immediately available for evaluation
```

---

## Key Services

1. **RuleParsingService**: AI extraction from documents
2. **RuleValidationTaskService**: Human validation workflow
3. **RulePublishingService**: Publishing to production ⭐ **NEW**
4. **RuleEngineService**: Evaluation of rules

---

## Files Created/Modified

1. **Created**: `src/rules_knowledge/services/rule_publishing_service.py`
   - Main publishing service
   - Handles automated and manual rule creation

2. **Modified**: `src/rules_knowledge/services/__init__.py`
   - Added `RulePublishingService` export

3. **Modified**: `src/data_ingestion/services/rule_validation_task_service.py`
   - Added auto-publish on approval (optional)

---

## Next Steps

1. ✅ Rule Publishing Service implemented
2. ⏳ Create API endpoints for publishing
3. ⏳ Add admin UI for rule management
4. ⏳ Add tests for publishing workflow
5. ⏳ Integrate with Vector DB update (when implemented)


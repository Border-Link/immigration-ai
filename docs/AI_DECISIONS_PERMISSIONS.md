# AI Decisions Module - Dedicated Permissions

**Date**: 2024-12-19  
**Reviewer**: Lead Principal Engineer

---

## Overview

Dedicated permission classes for the `ai_decisions` module provide clear, self-documenting access control specific to AI decisions functionality. These permissions are more explicit and maintainable than generic permissions.

---

## Permission Classes

### 1. Eligibility Result Permissions

#### `CanViewEligibilityResult`
**File**: `src/ai_decisions/permissions/eligibility_result_permissions.py`

**Purpose**: Permission to view eligibility results.

**Rules**:
- User owns the case (case.user == user)
- User is superuser
- User is reviewer (role='reviewer' AND is_staff/is_superuser)
- User is admin (role='admin' OR is_staff)

**Used By**:
- `EligibilityResultDetailAPI` - View specific eligibility result

**Usage**:
```python
permission_classes = [CanViewEligibilityResult]
```

---

#### `CanModifyEligibilityResult`
**File**: `src/ai_decisions/permissions/eligibility_result_permissions.py`

**Purpose**: Permission to modify (update/delete) eligibility results.

**Rules**:
- User owns the case (case.user == user)
- User is superuser
- User is admin (role='admin' OR is_staff)

**Note**: Reviewers do NOT have write access (read-only).

**Used By**:
- `EligibilityResultUpdateAPI` - Update eligibility result
- `EligibilityResultDeleteAPI` - Delete eligibility result

**Usage**:
```python
permission_classes = [CanModifyEligibilityResult]
```

---

### 2. AI Reasoning Log Permissions

#### `CanViewAIReasoningLog`
**File**: `src/ai_decisions/permissions/ai_reasoning_log_permissions.py`

**Purpose**: Permission to view AI reasoning logs (prompts, responses, tokens).

**Rules**:
- User is reviewer (role='reviewer' AND is_staff/is_superuser)
- User is admin/staff (is_staff OR is_superuser)

**Rationale**: AI reasoning logs contain sensitive information and are restricted to reviewers and admins for auditing and debugging purposes.

**Used By**:
- `AIReasoningLogListAPI` - List AI reasoning logs
- `AIReasoningLogDetailAPI` - View specific AI reasoning log

**Usage**:
```python
permission_classes = [CanViewAIReasoningLog]
```

---

### 3. AI Citation Permissions

#### `CanViewAICitation`
**File**: `src/ai_decisions/permissions/ai_citation_permissions.py`

**Purpose**: Permission to view AI citations (sources used by AI).

**Rules**:
- User is reviewer (role='reviewer' AND is_staff/is_superuser)
- User is admin/staff (is_staff OR is_superuser)

**Rationale**: AI citations are used for auditing and quality assurance, showing which sources the AI used in its reasoning. Restricted to reviewers and admins.

**Used By**:
- `AICitationListAPI` - List AI citations
- `AICitationDetailAPI` - View specific AI citation

**Usage**:
```python
permission_classes = [CanViewAICitation]
```

---

## Permission Matrix

| Resource | Regular User | Reviewer | Admin/Staff | Superuser |
|----------|--------------|----------|-------------|-----------|
| **Eligibility Results (View)** | Own cases | All cases | All cases | All cases |
| **Eligibility Results (Modify)** | Own cases | ❌ | All cases | All cases |
| **AI Reasoning Logs** | ❌ | ✅ | ✅ | ✅ |
| **AI Citations** | ❌ | ✅ | ✅ | ✅ |

---

## Benefits of Dedicated Permissions

### 1. **Self-Documenting**
- Permission class names clearly indicate what they control
- `CanViewEligibilityResult` is more explicit than `HasCaseOwnership`
- `CanModifyEligibilityResult` is more explicit than `HasCaseWriteAccess`

### 2. **Module-Specific**
- Permissions are scoped to `ai_decisions` module
- Easier to find and maintain
- Can be extended with module-specific logic

### 3. **Maintainability**
- Changes to AI decisions permissions don't affect other modules
- Clear separation of concerns
- Easier to test and debug

### 4. **Flexibility**
- Can add module-specific permission logic
- Can extend permissions for future requirements
- Can add logging/auditing specific to AI decisions

---

## File Structure

```
src/ai_decisions/
├── permissions/
│   ├── __init__.py
│   ├── eligibility_result_permissions.py
│   ├── ai_reasoning_log_permissions.py
│   └── ai_citation_permissions.py
└── views/
    ├── eligibility_result/
    ├── ai_reasoning_log/
    └── ai_citation/
```

---

## Migration from Generic Permissions

### Before (Generic)
```python
from main_system.permissions.has_case_ownership import HasCaseOwnership, HasCaseWriteAccess
from main_system.permissions.is_reviewer import IsReviewer

permission_classes = [HasCaseOwnership]  # Generic, not specific to eligibility results
permission_classes = [IsReviewer]  # Generic, not specific to AI reasoning logs
```

### After (Dedicated)
```python
from ai_decisions.permissions.eligibility_result_permissions import (
    CanViewEligibilityResult,
    CanModifyEligibilityResult
)
from ai_decisions.permissions.ai_reasoning_log_permissions import CanViewAIReasoningLog
from ai_decisions.permissions.ai_citation_permissions import CanViewAICitation

permission_classes = [CanViewEligibilityResult]  # Specific to eligibility results
permission_classes = [CanViewAIReasoningLog]  # Specific to AI reasoning logs
```

---

## Implementation Details

### Eligibility Result Permissions
- **Base**: Uses `CaseOwnershipPermission` helper internally
- **Object-level**: Checks `obj.case` for ownership
- **Read access**: User owns case OR is reviewer/admin/superuser
- **Write access**: User owns case OR is admin/superuser (NOT reviewers)

### AI Reasoning Log Permissions
- **Base**: Combines `IsReviewer` OR `IsAdminOrStaff`
- **View-level**: Checks role and staff status
- **Object-level**: Same as view-level (all logs accessible if permission granted)

### AI Citation Permissions
- **Base**: Combines `IsReviewer` OR `IsAdminOrStaff`
- **View-level**: Checks role and staff status
- **Object-level**: Same as view-level (all citations accessible if permission granted)

---

## Summary

✅ **Created dedicated permission classes for ai_decisions module**
- `CanViewEligibilityResult` - View eligibility results
- `CanModifyEligibilityResult` - Modify eligibility results
- `CanViewAIReasoningLog` - View AI reasoning logs
- `CanViewAICitation` - View AI citations

✅ **Updated all views to use dedicated permissions**
- All eligibility result views updated
- All AI reasoning log views updated
- All AI citation views updated

✅ **Benefits**
- Self-documenting permission names
- Module-specific permissions
- Better maintainability
- Clear separation of concerns

**Status**: ✅ **COMPLETE**

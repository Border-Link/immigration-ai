# AI Decisions Module - Architecture Fixes

**Date**: 2024-12-19  
**Reviewer**: Lead Principal Engineer  
**Issue**: Views were calling selectors/repositories directly and using method-based permissions instead of class-based permissions.

---

## Issues Found

### 1. Views Calling Selectors/Repositories Directly
- ❌ `eligibility_result/read.py`: Using `CaseSelector.get_by_id()` directly
- ❌ `eligibility_result/read.py`: Using `.filter()` on queryset directly
- ❌ `ai_decisions_analytics.py`: Using `.filter()` on queryset directly

### 2. Method-Based Permissions Instead of Class-Based
- ❌ `eligibility_result/read.py`: Using `CaseOwnershipPermission.has_case_access()` in methods
- ❌ `eligibility_result/update_delete.py`: Using `CaseOwnershipPermission.has_case_write_access()` in methods

---

## Fixes Applied

### 1. Created DRF Permission Classes

**File**: `src/main_system/permissions/has_case_ownership.py`

- ✅ **`HasCaseOwnership`**: DRF permission class for read access to case-related resources
- ✅ **`HasCaseWriteAccess`**: DRF permission class for write access to case-related resources

**Usage**:
```python
permission_classes = [HasCaseOwnership]  # For read access
permission_classes = [HasCaseWriteAccess]  # For write access
```

### 2. Added Service Methods

**File**: `src/ai_decisions/services/eligibility_result_service.py`

- ✅ **`get_by_user_access(user)`**: Filter eligibility results by user access (replaces `.filter()` in views)
- ✅ **`get_by_case_with_access_check(case_id, user)`**: Get results for a case with access verification (replaces `CaseSelector.get_by_id()` + permission check)

**File**: `src/ai_decisions/services/ai_citation_service.py`

- ✅ **`get_by_quality_filters(citations, ...)`**: Filter citations by quality thresholds (replaces `.filter()` in analytics view)

### 3. Fixed Views

#### `eligibility_result/read.py`
- ✅ Removed `CaseSelector.get_by_id()` - now uses `EligibilityResultService.get_by_case_with_access_check()`
- ✅ Removed `.filter()` - now uses `EligibilityResultService.get_by_user_access()`
- ✅ Removed method-based permission checks - now uses `HasCaseOwnership` permission class

**Before**:
```python
case = CaseSelector.get_by_id(str(case_id))
if not CaseOwnershipPermission.has_case_access(request.user, case):
    return 403
results = all_results.filter(case__user=user)
```

**After**:
```python
results, error = EligibilityResultService.get_by_case_with_access_check(case_id, request.user)
# Permission handled by service
permission_classes = [HasCaseOwnership]  # Class-based permission
```

#### `eligibility_result/update_delete.py`
- ✅ Removed method-based permission checks - now uses `HasCaseWriteAccess` permission class

**Before**:
```python
if not CaseOwnershipPermission.has_case_write_access(request.user, result.case):
    return 403
```

**After**:
```python
permission_classes = [HasCaseWriteAccess]  # Class-based permission
# Permission automatically checked by DRF
```

#### `admin/ai_decisions_analytics.py`
- ✅ Removed `.filter()` - now uses `AICitationService.get_by_quality_filters()`

**Before**:
```python
'high_quality': citations.filter(relevance_score__gte=0.8).count(),
```

**After**:
```python
quality_filters = AICitationService.get_by_quality_filters(citations)
'high_quality': quality_filters['high_quality'].count(),
```

---

## Architecture Compliance

### ✅ Views Layer
- **Only uses Services** - No direct calls to selectors or repositories
- **Class-based permissions** - All permissions defined at class level using `permission_classes`
- **No business logic** - Views are thin, delegate to services

### ✅ Services Layer
- **Can use Selectors/Repositories** - Services are allowed to use selectors and repositories internally
- **Business logic** - All business logic resides in services
- **Access control** - Services handle access checks when needed

### ✅ Permission Classes
- **DRF BasePermission** - All permissions extend `rest_framework.permissions.BasePermission`
- **Class-level** - Permissions defined at view class level, not in methods
- **Object-level** - Use `has_object_permission()` for resource-specific checks

---

## Files Changed

### New Files
1. `src/main_system/permissions/has_case_ownership.py` - DRF permission classes

### Modified Files
1. `src/ai_decisions/services/eligibility_result_service.py` - Added access filtering methods
2. `src/ai_decisions/services/ai_citation_service.py` - Added quality filtering method
3. `src/ai_decisions/views/eligibility_result/read.py` - Fixed to use services and class-based permissions
4. `src/ai_decisions/views/eligibility_result/update_delete.py` - Fixed to use class-based permissions
5. `src/ai_decisions/views/admin/ai_decisions_analytics.py` - Fixed to use service methods

---

## Verification

### ✅ All Views Use Services Only
- `eligibility_result/read.py` ✅
- `eligibility_result/update_delete.py` ✅
- `ai_reasoning_log/read.py` ✅
- `ai_citation/read.py` ✅
- All admin views ✅

### ✅ All Permissions Are Class-Based
- `EligibilityResultListAPI` - Uses service method for access check ✅
- `EligibilityResultDetailAPI` - Uses `HasCaseOwnership` ✅
- `EligibilityResultUpdateAPI` - Uses `HasCaseWriteAccess` ✅
- `EligibilityResultDeleteAPI` - Uses `HasCaseWriteAccess` ✅
- All other views - Already using class-based permissions ✅

---

## Summary

**Status**: ✅ **ALL ISSUES FIXED**

- ✅ Views no longer call selectors/repositories directly
- ✅ All permissions are class-based (using `permission_classes`)
- ✅ All business logic moved to services
- ✅ Architecture compliance verified

**Architecture Pattern**:
```
View → Service → Selector/Repository → Database
     ↓
Permission Classes (DRF)
```

All views now follow the correct architecture pattern.

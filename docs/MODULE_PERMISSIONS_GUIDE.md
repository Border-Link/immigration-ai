# Module Permissions Guide

**Date**: 2024-12-19  
**Status**: ✅ **COMPLETE**

---

## Overview

Comprehensive DRF permission classes for all system modules based on `ROLE_TO_IMPLEMENT.md`. Each permission class handles both module-level (`has_permission`) and object-level (`has_object_permission`) checks.

---

## Permission Classes

### 1. Authentication Module

**Class**: `AuthenticationPermission`

**Permissions**:
- **User**: Register, login, reset password
- **Reviewer**: Login
- **Staff**: Login, create users
- **Super Admin**: Full user management (CRUD users, assign roles)

**Object-level**: Users can manage their own account. Staff/Superadmin can manage any account.

**Usage**:
```python
from main_system.permissions.authentication_permissions import AuthenticationPermission

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [AuthenticationPermission]
```

---

### 2. Case Management Module

**Class**: `CasePermission`

**Permissions**:
- **User**: Create case, Submit facts, Retrieve own cases
- **Reviewer**: Retrieve assigned cases, Add review notes
- **Staff**: Retrieve all cases, Update case status (limited)
- **Super Admin**: Full CRUD on all cases

**Object-level**: Based on case ownership or assignment.

**Usage**:
```python
from main_system.permissions.case_permissions import CasePermission

class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [CasePermission]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'user':
            return Case.objects.filter(user=user)
        elif user.role == 'reviewer':
            # Reviewers see assigned cases
            return Case.objects.filter(reviews__reviewer=user).distinct()
        return Case.objects.all()  # Staff/Superadmin see all
```

**Class**: `CaseFactPermission`

**Permissions**: Users can submit/update facts for their own cases. Reviewers/Staff/Superadmin can view facts for cases they have access to.

---

### 3. Rule Engine Module

**Class**: `RulePermission`

**Permissions**:
- **User**: Run eligibility checks (read-only, cannot modify rules)
- **Reviewer**: Read-only (see rule outcomes)
- **Staff**: Create/edit rules (limited to staging, maybe)
- **Super Admin**: Full rule management (publish, archive, override)

**Usage**:
```python
from main_system.permissions.rule_permissions import RulePermission

class RuleViewSet(viewsets.ModelViewSet):
    permission_classes = [RulePermission]
```

---

### 4. Document Service Module

**Class**: `DocumentPermission`

**Permissions**:
- **User**: Upload documents, View own documents
- **Reviewer**: Access documents for assigned cases, Validate document classification
- **Staff**: Access all documents, Delete/reclassify documents
- **Super Admin**: Full access to all documents and storage settings

**Object-level**: Based on case ownership or assignment.

**Usage**:
```python
from main_system.permissions.document_permissions import DocumentPermission

class CaseDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [DocumentPermission]
```

---

### 5. AI Reasoning Service Module

**Class**: `AIReasoningPermission`

**Permissions**:
- **User**: Trigger AI reasoning for own cases (read-only results)
- **Reviewer**: Access AI outputs for assigned cases
- **Staff**: View AI logs, cannot edit
- **Super Admin**: Full access to AI logs, LLM prompts, embeddings

**Object-level**: Access tied to case ownership/assignment.

**Usage**:
```python
from main_system.permissions.ai_reasoning_permissions import AIReasoningPermission

class AIReasoningLogViewSet(viewsets.ModelViewSet):
    permission_classes = [AIReasoningPermission]
```

---

### 6. Ingestion Service Module

**Class**: `IngestionPermission`

**Permissions**:
- **User**: No access
- **Reviewer**: No access
- **Staff**: Monitor ingestion status
- **Super Admin**: Full ingestion service management (scheduler, rule parsing, publishing)

**Object-level**: Based on assignment or superadmin access.

**Usage**:
```python
from main_system.permissions.ingestion_permissions import IngestionPermission

class DataSourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IngestionPermission]
```

---

### 7. Review Service Module

**Class**: `ReviewPermission`

**Permissions**:
- **User**: Request review (manual escalation)
- **Reviewer**: Access assigned review tasks, Approve/reject/override, Add notes
- **Staff**: Monitor reviews
- **Super Admin**: Full review management, reassign reviewers, audit reviews

**Object-level**: Based on review assignment or case ownership.

**Usage**:
```python
from main_system.permissions.review_permissions import ReviewPermission

class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [ReviewPermission]
```

**Class**: `ReviewNotePermission`

**Permissions**: Reviewers can add notes to assigned reviews. Users can view notes for their own case reviews. Staff/Superadmin can view all notes.

**Class**: `DecisionOverridePermission`

**Permissions**: Reviewers can create overrides for assigned reviews. Users can view overrides for their own cases. Staff/Superadmin can view all overrides.

---

### 8. Admin Console Module

**Class**: `AdminPermission`

**Permissions**:
- **User**: No access
- **Reviewer**: No access
- **Staff**: Limited admin tasks (e.g., audit logs, rule validation tasks)
- **Super Admin**: Full admin console access

**Usage**:
```python
from main_system.permissions.admin_permissions import AdminPermission

class AdminDashboardViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminPermission]
```

---

### 9. Payment Module

**Class**: `PaymentPermission`

**Permissions**: Users can view and create payments for their own cases. Staff/Superadmin can view all payments.

**Object-level**: Based on case ownership.

**Usage**:
```python
from main_system.permissions.payment_permissions import PaymentPermission

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [PaymentPermission]
```

---

### 10. Rule Validation Task Module

**Class**: `RuleValidationTaskPermission`

**Permissions**:
- **Staff**: Monitor ingestion status (includes rule validation tasks)
- **Super Admin**: Full ingestion service management

Reviewers can access tasks assigned to them.

**Usage**:
```python
from main_system.permissions.rule_validation_permissions import RuleValidationTaskPermission

class RuleValidationTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [RuleValidationTaskPermission]
```

---

## Role Hierarchy

The permission system follows this hierarchy:

1. **Super Admin** (`is_superuser=True`): Full access to everything
2. **Staff** (`is_staff=True` OR `role='admin'`): Access to most admin functions
3. **Reviewer** (`role='reviewer'` AND `is_staff/is_superuser`): Access to assigned cases and reviews
4. **User** (`role='user'`): Access to own cases and data

---

## Implementation Pattern

### Basic Usage

```python
from rest_framework import viewsets
from main_system.permissions.case_permissions import CasePermission

class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [CasePermission]
```

### Queryset Filtering

Always filter querysets to prevent users from seeing objects they cannot access:

```python
def get_queryset(self):
    user = self.request.user
    
    # Superadmin/Staff see all
    if user.is_superuser or user.is_staff or user.role == 'admin':
        return Case.objects.all()
    
    # Reviewer sees assigned cases
    if user.role == 'reviewer' and (user.is_staff or user.is_superuser):
        return Case.objects.filter(reviews__reviewer=user).distinct()
    
    # User sees own cases
    return Case.objects.filter(user=user)
```

### Combining Permissions

You can combine permissions using DRF's permission operators:

```python
from rest_framework.permissions import IsAuthenticated
from main_system.permissions.module_permissions import CasePermission

class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CasePermission]
```

---

## Permission Matrix

| Module | User | Reviewer | Staff | Super Admin |
|--------|------|----------|-------|-------------|
| **Authentication** | Register, Login, Reset Password | Login | Login, Create Users | Full User Management |
| **Case Management** | Create, View Own | View Assigned | View All, Update Status | Full CRUD |
| **Rule Engine** | Run Checks (Read-only) | Read-only | Create/Edit Rules | Full Management |
| **Document Service** | Upload, View Own | View Assigned, Validate | View All, Delete/Reclassify | Full Access |
| **AI Reasoning** | Trigger for Own (Read-only) | View Assigned | View Logs (Read-only) | Full Access |
| **Ingestion Service** | No Access | No Access | Monitor Status | Full Management |
| **Review Service** | Request Review | Access Assigned, Approve/Reject | Monitor Reviews | Full Management |
| **Admin Console** | No Access | No Access | Limited Tasks | Full Access |
| **Payment** | Create, View Own | View Assigned | View All | Full Access |

---

## Best Practices

1. **Always use queryset filtering**: Even with object-level permissions, filter querysets to prevent unnecessary database queries.

2. **Combine with role-based permissions**: Use module permissions for object-level checks, and role-based permissions (`IsUser`, `IsReviewer`, etc.) for view-level checks.

3. **Test permissions thoroughly**: Ensure users can only access what they should, and cannot bypass permissions.

4. **Document permission logic**: Add comments explaining why certain permissions are granted or denied.

5. **Use SAFE_METHODS**: Distinguish between read (GET, HEAD, OPTIONS) and write (POST, PUT, PATCH, DELETE) operations.

---

## File Structure

All permissions are organized by concern in separate files:

### Base Permissions (Common Logic)
- `src/main_system/permissions/base_permissions.py`
  - `RoleChecker` - Class-based role checking utilities
  - `CaseOwnershipMixin` - Mixin for case ownership checks
  - `BaseModulePermission` - Base class for all module permissions

### Module-Specific Permissions
- `src/main_system/permissions/authentication_permissions.py` - Authentication module
- `src/main_system/permissions/case_permissions.py` - Case management module
- `src/main_system/permissions/rule_permissions.py` - Rule engine module
- `src/main_system/permissions/document_permissions.py` - Document service module
- `src/main_system/permissions/ai_reasoning_permissions.py` - AI reasoning module
- `src/main_system/permissions/ingestion_permissions.py` - Ingestion service module
- `src/main_system/permissions/review_permissions.py` - Review service module
- `src/main_system/permissions/admin_permissions.py` - Admin console module
- `src/main_system/permissions/payment_permissions.py` - Payment module
- `src/main_system/permissions/rule_validation_permissions.py` - Rule validation tasks

### Role-Based Permissions
- `src/main_system/permissions/is_user.py`
- `src/main_system/permissions/is_reviewer.py`
- `src/main_system/permissions/is_staff.py`
- `src/main_system/permissions/is_superadmin.py`

---

## Summary

✅ **All module permissions implemented**
- Authentication Module ✅
- Case Management Module ✅
- Rule Engine Module ✅
- Document Service Module ✅
- AI Reasoning Service Module ✅
- Ingestion Service Module ✅
- Review Service Module ✅
- Admin Console Module ✅
- Payment Module ✅
- Rule Validation Task Module ✅

✅ **Both module-level and object-level checks**
✅ **Follows ROLE_TO_IMPLEMENT.md specification**
✅ **Compatible with existing User model structure**

**Status**: ✅ **COMPLETE**

# Automatic Eligibility Check Triggers

## Overview

Eligibility checks should be **automatically triggered** by the system at appropriate times. Regular users **cannot** manually request eligibility checks. Only reviewers and admins can manually request eligibility checks for review purposes.

---

## Who Can Request Eligibility Checks?

### ❌ **Regular Users - CANNOT Request**
- Regular users cannot manually request eligibility checks
- This prevents abuse, spam, and unnecessary API calls
- Users should wait for automatic checks

### ✅ **Reviewers - CAN Request**
- Reviewers can manually request eligibility checks for any case
- Used for re-evaluation during review process
- Endpoint: `POST /api/v1/cases/{case_id}/eligibility`

### ✅ **Admins/Staff - CAN Request**
- Admins and staff can manually request eligibility checks for any case
- Used for system maintenance, debugging, and re-evaluation
- Endpoint: `POST /api/v1/cases/{case_id}/eligibility`

---

## When Should Eligibility Checks Be Automatically Triggered?

### 1. **Case Submission** (Recommended)
When a user submits their case (status changes to `'submitted'` or `'pending_review'`):
- Trigger eligibility check automatically
- Evaluate all active visa types for the case's jurisdiction
- Store results for reviewer to see

**Implementation Location**: `src/immigration_cases/signals/case_signals.py` or `src/immigration_cases/services/case_service.py`

**Example**:
```python
# In case_service.py or case_signals.py
if case.status == 'submitted':
    # Trigger eligibility check automatically
    from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task
    run_eligibility_check_task.delay(str(case.id))
```

### 2. **Document Processing Completion** (Recommended)
When all required documents for a case are processed and verified:
- Trigger eligibility check automatically
- Re-evaluate eligibility with new document information
- Update existing eligibility results if needed

**Implementation Location**: `src/document_handling/tasks/document_tasks.py` or `src/document_handling/signals/document_signals.py`

**Example**:
```python
# In document_tasks.py after document processing
if all_documents_verified:
    from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task
    run_eligibility_check_task.delay(str(case.id))
```

### 3. **Case Facts Update** (Optional)
When critical case facts are updated (e.g., salary, age, nationality):
- Consider triggering eligibility check if facts affect eligibility
- May want to debounce this (don't check on every fact update)

**Implementation Location**: `src/immigration_cases/services/case_fact_service.py`

### 4. **Payment Completion** (Optional)
When a user completes payment for a case:
- Trigger eligibility check automatically
- Ensures eligibility is evaluated after payment is confirmed

**Implementation Location**: `src/payments/services/payment_service.py` or `src/payments/views/webhooks/`

---

## Current Implementation Status

### ✅ **Manual Request Endpoint**
- **Endpoint**: `POST /api/v1/cases/{case_id}/eligibility`
- **Permission**: `IsReviewerOrAdmin` (reviewers and admins only)
- **Status**: ✅ **IMPLEMENTED**

### ⚠️ **Automatic Triggers**
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Action Required**: Add automatic triggers in the locations mentioned above

---

## Recommended Implementation

### Step 1: Add Signal Handler for Case Submission

**File**: `src/immigration_cases/signals/case_signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from immigration_cases.models.case import Case
from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task
import logging

logger = logging.getLogger('django')


@receiver(post_save, sender=Case)
def handle_case_submitted(sender, instance, created, **kwargs):
    """
    Trigger eligibility check when case is submitted.
    """
    # Only trigger if case status changed to 'submitted' or 'pending_review'
    if instance.status in ['submitted', 'pending_review']:
        logger.info(f"Case {instance.id} submitted - triggering automatic eligibility check")
        run_eligibility_check_task.delay(str(instance.id))
```

### Step 2: Add Trigger in Document Processing

**File**: `src/document_handling/tasks/document_tasks.py`

```python
# After document processing completes successfully
# Check if all required documents are verified
from document_handling.services.document_checklist_service import DocumentChecklistService
from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task

# At the end of process_document_task
all_required_documents_verified = DocumentChecklistService.check_all_required_documents_verified(case_id)

if all_required_documents_verified:
    logger.info(f"All documents verified for case {case_id} - triggering automatic eligibility check")
    run_eligibility_check_task.delay(case_id)
```

### Step 3: Add Trigger on Payment Completion

**File**: `src/payments/services/payment_service.py` or `src/payments/views/webhooks/`

```python
# After payment status changes to 'completed'
if payment.status == 'completed' and payment.case:
    logger.info(f"Payment completed for case {payment.case.id} - triggering automatic eligibility check")
    from ai_decisions.tasks.ai_reasoning_tasks import run_eligibility_check_task
    run_eligibility_check_task.delay(str(payment.case.id))
```

---

## Benefits of Automatic Triggers

1. **Better User Experience**: Users don't need to manually request checks
2. **Consistency**: Eligibility is always evaluated at the right time
3. **Security**: Prevents abuse and spam from manual requests
4. **Automation**: System handles eligibility evaluation automatically
5. **Reviewer Efficiency**: Reviewers see eligibility results immediately when reviewing cases

---

## Summary

- ✅ **Manual requests**: Only reviewers and admins can request eligibility checks
- ⚠️ **Automatic triggers**: Need to be implemented for case submission, document processing, and payment completion
- **Next Steps**: Implement automatic triggers in the recommended locations

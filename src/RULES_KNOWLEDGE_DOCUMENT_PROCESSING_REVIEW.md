# Rules Knowledge & Document Processing - Comprehensive Architecture Review

**Reviewer:** Lead Principal Engineer  
**Date:** 2024  
**Scope:** `rules_knowledge` and `document_processing` directories  
**Status:** Comprehensive Review & Recommendations

---

## Executive Summary

This review examines the `rules_knowledge` and `document_processing` directories against requirements in `implementation.md` and `IMPLEMENTATION_STATUS.md`. The review identifies architectural gaps, missing features, design improvements, and critical enhancements needed for production readiness.

**Overall Assessment**: 
- **rules_knowledge**: ✅ **Well-Architected** with some critical gaps
- **document_processing**: ✅ **Well-Architected** but underutilized

---

## 1. Rules Knowledge Directory Review

### 1.1 Architecture Compliance ✅

**Strengths:**
- ✅ Proper separation: Repositories (write), Selectors (read), Services (business logic)
- ✅ Views call services, services call selectors/repositories
- ✅ No direct model access in services
- ✅ Comprehensive admin functionality implemented
- ✅ Proper serialization with error handling
- ✅ Consistent error handling patterns

### 1.2 Critical Missing Features

#### ❌ **1.2.1 Database Constraints for Rule Version Overlaps**

**Issue**: No database-level constraint preventing overlapping effective date ranges for the same visa type.

**Current State**:
- `VisaRuleVersionRepository.create_rule_version()` attempts to close previous versions
- `RulePublishingService._close_previous_version()` handles overlaps
- BUT: No database constraint prevents race conditions or manual creation of overlapping versions

**Risk**: **HIGH** - Can lead to ambiguous rule evaluation results

**Recommendation**:
```python
# Add to VisaRuleVersion.Meta:
constraints = [
    models.CheckConstraint(
        check=Q(effective_to__isnull=True) | Q(effective_to__gte=F('effective_from')),
        name='effective_to_after_effective_from'
    ),
    # Note: Overlap prevention requires application-level logic or database triggers
    # PostgreSQL exclusion constraints could be used:
    # EXCLUDE USING gist (visa_type_id WITH =, tstzrange(effective_from, effective_to) WITH &&)
]
```

**Action Required**: Add database migration with exclusion constraint or application-level validation service.

---

#### ❌ **1.2.2 JSON Logic Expression Validation**

**Issue**: No validation of JSON Logic expressions when creating/updating `VisaRequirement`.

**Current State**:
- `RuleEngineService.validate_expression_structure()` exists but is only called during evaluation
- No validation in `VisaRequirementRepository` or serializers
- Invalid expressions can be stored and only fail at evaluation time

**Risk**: **MEDIUM** - Invalid expressions stored in database, discovered only during eligibility checks

**Recommendation**:
```python
# Add to rules_knowledge/helpers/json_logic_validator.py
class JSONLogicValidator:
    @staticmethod
    def validate_expression(expression: dict) -> Tuple[bool, Optional[str]]:
        """Validate JSON Logic expression structure and syntax."""
        # Use existing RuleEngineService.validate_expression_structure()
        # Add syntax validation
        # Test with sample data
        pass

# Add to VisaRequirementRepository.create_requirement():
# - Validate expression before saving
# - Raise ValidationError if invalid
```

**Action Required**: Create validation helper and integrate into repository layer.

---

#### ❌ **1.2.3 Requirement Code Uniqueness Constraint**

**Issue**: No uniqueness constraint on `requirement_code` per `rule_version`.

**Current State**:
- `requirement_code` is just indexed, not unique
- Multiple requirements with same code can exist for same rule version
- Can cause confusion and evaluation issues

**Risk**: **MEDIUM** - Ambiguous requirements, potential evaluation conflicts

**Recommendation**:
```python
# Add to VisaRequirement.Meta:
unique_together = [['rule_version', 'requirement_code']]
```

**Action Required**: Add database migration.

---

#### ❌ **1.2.4 Rule Version Effective Date Validation**

**Issue**: No validation that `effective_from` is not in the past when creating published rules.

**Current State**:
- Can create rule versions with `effective_from` in the past
- Can create published rules retroactively
- No validation in service layer

**Risk**: **LOW** - May be intentional for historical rule creation, but should be explicit

**Recommendation**:
```python
# Add to VisaRuleVersionService.create_rule_version():
if is_published and effective_from < timezone.now() - timedelta(days=1):
    logger.warning(f"Creating published rule version with past effective_from: {effective_from}")
    # Optionally raise ValidationError or require admin override
```

**Action Required**: Add validation with admin override option.

---

#### ❌ **1.2.5 Soft Delete for Rule Versions**

**Issue**: Hard delete of rule versions can break historical eligibility results.

**Current State**:
- `VisaRuleVersionRepository.delete_rule_version()` performs hard delete
- Historical eligibility results reference deleted rule versions
- No audit trail of deleted rules

**Risk**: **HIGH** - Data integrity issues, broken references, loss of audit trail

**Recommendation**:
```python
# Add to VisaRuleVersion model:
deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
is_deleted = models.BooleanField(default=False, db_index=True)

# Update repository:
def delete_rule_version(rule_version):
    """Soft delete rule version."""
    with transaction.atomic():
        # Check if referenced by eligibility results
        from ai_decisions.selectors.eligibility_result_selector import EligibilityResultSelector
        results = EligibilityResultSelector.get_by_rule_version(rule_version.id)
        if results.exists():
            raise ValidationError(
                f"Cannot delete rule version {rule_version.id}: "
                f"referenced by {results.count()} eligibility results"
            )
        
        rule_version.is_deleted = True
        rule_version.deleted_at = timezone.now()
        rule_version.save()
```

**Action Required**: Implement soft delete with reference checking.

---

#### ❌ **1.2.6 Rule Version Change History/Audit Trail**

**Issue**: No tracking of who changed rule versions and when.

**Current State**:
- `created_at` and `updated_at` exist but no user tracking
- No audit log for rule changes
- Cannot track who published/unpublished rules

**Risk**: **MEDIUM** - Compliance and audit requirements

**Recommendation**:
```python
# Add to VisaRuleVersion model:
created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name='created_rule_versions'
)
updated_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name='updated_rule_versions'
)
published_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name='published_rule_versions'
)
published_at = models.DateTimeField(null=True, blank=True)

# Or use audit log service (if exists)
```

**Action Required**: Add user tracking fields or integrate with audit log service.

---

#### ✅ **1.2.7 Conditional Document Requirements Evaluation** - **VERIFIED IMPLEMENTED**

**Status**: ✅ **FULLY IMPLEMENTED**

**Current State**:
- ✅ `conditional_logic` field exists (JSON Logic)
- ✅ `DocumentRequirementMatchingService.match_document_against_requirements()` evaluates conditional logic
- ✅ `DocumentChecklistService.generate_checklist()` evaluates conditional logic
- ✅ Uses `RuleEngineService.evaluate_expression()` for evaluation
- ✅ Proper error handling with fallback to default behavior

**Implementation**: Verified in:
- `document_handling/services/document_requirement_matching_service.py` (lines 102-126)
- `document_handling/services/document_checklist_service.py` (lines 114-141)

**Note**: The implementation defaults to "passed" when evaluation has errors or missing facts. Consider making this configurable or more explicit.

---

### 1.3 Design Improvements

#### ⚠️ **1.3.1 Rule Version Conflict Detection**

**Current**: Overlap detection happens during creation but not proactively.

**Improvement**: Add service method to detect and report conflicts:
```python
@staticmethod
def detect_version_conflicts(visa_type_id: str, effective_from: datetime, effective_to: Optional[datetime] = None) -> List[Dict]:
    """Detect overlapping rule versions before creation."""
    # Query for overlapping versions
    # Return list of conflicts with details
```

---

#### ⚠️ **1.3.2 Rule Version Comparison/Diff**

**Missing**: No way to compare two rule versions to see what changed.

**Recommendation**: Add service method:
```python
@staticmethod
def compare_rule_versions(version1_id: str, version2_id: str) -> Dict:
    """Compare two rule versions and return differences."""
    # Compare requirements
    # Compare document requirements
    # Return structured diff
```

---

#### ⚠️ **1.3.3 Bulk Rule Version Operations**

**Missing**: No bulk operations for rule versions (bulk publish, bulk close, etc.).

**Recommendation**: Add to admin views (similar to other bulk operations).

---

#### ⚠️ **1.3.4 Rule Version Rollback**

**Missing**: No ability to rollback to previous rule version.

**Recommendation**: Add service method:
```python
@staticmethod
def rollback_to_version(version_id: str, rollback_to_version_id: str) -> Dict:
    """Rollback current version to a previous version."""
    # Close current version
    # Reopen previous version
    # Create audit log entry
```

---

### 1.4 Performance & Scalability

#### ⚠️ **1.4.1 Caching for Active Rule Versions**

**Issue**: `get_current_by_visa_type()` is called frequently but not cached.

**Recommendation**: Add caching layer:
```python
from django.core.cache import cache

@staticmethod
def get_current_by_visa_type(visa_type_id: str, use_cache: bool = True):
    cache_key = f"current_rule_version:{visa_type_id}"
    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            return cached
    
    version = VisaRuleVersionSelector.get_current_by_visa_type(visa_type)
    if use_cache and version:
        cache.set(cache_key, version, timeout=3600)  # 1 hour
    return version
```

---

#### ⚠️ **1.4.2 Index Optimization**

**Current Indexes**: Good coverage but could be optimized:
- Add composite index: `(visa_type, is_published, effective_from, effective_to)` for current version queries
- Add partial index: `WHERE is_published = TRUE` for published versions

---

### 1.5 Testing Gaps

**Missing**:
- ❌ Unit tests for rule version overlap detection
- ❌ Unit tests for JSON Logic validation
- ❌ Integration tests for rule publishing workflow
- ❌ Edge case tests for requirement evaluation
- ❌ Performance tests for rule engine with large requirement sets

---

## 2. Document Processing Directory Review

### 2.1 Architecture Compliance ✅

**Strengths:**
- ✅ Proper separation: Repositories, Selectors, Services
- ✅ Comprehensive admin functionality
- ✅ Good model design with proper indexes
- ✅ Processing history tracking

### 2.2 Critical Missing Features

#### ✅ **2.2.1 Integration with Document Handling** - **VERIFIED IMPLEMENTED**

**Status**: ✅ **FULLY INTEGRATED**

**Current State**: 
- ✅ `process_document_task` creates `ProcessingJob` records
- ✅ All processing steps log to `ProcessingHistory`
- ✅ Celery task IDs properly tracked
- ✅ Processing job status updated throughout workflow
- ✅ History entries created for each processing step

**Implementation**: Verified in `document_handling/tasks/document_tasks.py`:
```python
# In process_document_task:
from document_processing.services.processing_job_service import ProcessingJobService
from document_processing.services.processing_history_service import ProcessingHistoryService

# Create processing job
job = ProcessingJobService.create_processing_job(
    case_document_id=str(document.id),
    processing_type='full',
    celery_task_id=task.request.id,
    metadata={'task_name': 'process_document_task'}
)

# Log history entries for each step
ProcessingHistoryService.log_action(
    case_document_id=str(document.id),
    processing_job_id=str(job.id),
    action='ocr_started',
    status='success'
)
```

---

#### ❌ **2.2.2 Processing Job Retry Logic**

**Issue**: `retry_count` and `max_retries` fields exist but no automatic retry service.

**Current State**:
- Fields exist in model
- No service method to handle retries
- No Celery task retry integration

**Risk**: **MEDIUM** - Failed jobs not automatically retried

**Recommendation**: Create retry service:
```python
class ProcessingJobRetryService:
    @staticmethod
    def should_retry(job: ProcessingJob) -> bool:
        """Check if job should be retried."""
        return job.status == 'failed' and job.retry_count < job.max_retries
    
    @staticmethod
    def retry_job(job_id: str) -> Optional[ProcessingJob]:
        """Retry a failed processing job."""
        # Increment retry count
        # Reset status to pending
        # Queue new Celery task
        # Log retry attempt
```

---

#### ❌ **2.2.3 Processing Job Priority Queue**

**Issue**: `priority` field exists but no priority-based queue processing.

**Current State**:
- Priority field in model
- No Celery queue prioritization
- No service to manage priority queues

**Risk**: **LOW** - Nice to have, not critical

**Recommendation**: Use Celery priority queues:
```python
# In Celery task:
@shared_task(bind=True, priority=5)
def process_document_task(self, document_id: str, priority: int = 5):
    # Use priority parameter
    pass

# In service:
ProcessingJobService.create_processing_job(
    ...,
    priority=priority  # 1-10, higher is more urgent
)
```

---

#### ❌ **2.2.4 Processing Job Timeout Handling**

**Issue**: No timeout tracking or handling for stuck jobs.

**Current State**:
- `started_at` field exists
- No timeout detection
- No automatic cancellation of stuck jobs

**Risk**: **MEDIUM** - Jobs can get stuck indefinitely

**Recommendation**: Add timeout detection:
```python
@staticmethod
def detect_stuck_jobs(timeout_minutes: int = 60) -> QuerySet:
    """Detect processing jobs that have been running too long."""
    cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
    return ProcessingJob.objects.filter(
        status='processing',
        started_at__lt=cutoff
    )

# Add Celery task to run periodically:
@shared_task
def cleanup_stuck_jobs():
    """Cancel jobs that have been processing too long."""
    stuck_jobs = ProcessingJobService.detect_stuck_jobs()
    for job in stuck_jobs:
        ProcessingJobService.update_status(
            str(job.id),
            'failed',
            error_message='Job timeout',
            error_type='timeout'
        )
```

---

#### ❌ **2.2.5 Processing Job Cost Tracking**

**Issue**: `metadata` field exists but no structured cost tracking.

**Current State**:
- Metadata is JSONField (flexible but unstructured)
- No standardized cost tracking
- Cannot easily aggregate costs

**Risk**: **LOW** - Cost tracking is nice to have

**Recommendation**: Add structured cost fields or metadata schema:
```python
# Option 1: Add fields
llm_tokens_used = models.IntegerField(null=True, blank=True)
llm_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
ocr_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

# Option 2: Standardize metadata schema
metadata = {
    'costs': {
        'llm': {'tokens': 1000, 'cost_usd': 0.002},
        'ocr': {'pages': 5, 'cost_usd': 0.05}
    },
    'processing_time_ms': 1500,
    'confidence_scores': {...}
}
```

---

### 2.3 Design Improvements

#### ⚠️ **2.3.1 Processing Job Status Transitions**

**Issue**: No validation of status transitions.

**Recommendation**: Add state machine validation:
```python
VALID_TRANSITIONS = {
    'pending': ['queued', 'cancelled'],
    'queued': ['processing', 'cancelled'],
    'processing': ['completed', 'failed', 'cancelled'],
    'completed': [],  # Terminal
    'failed': ['pending'],  # Can retry
    'cancelled': []  # Terminal
}

def validate_status_transition(current: str, new: str) -> bool:
    return new in VALID_TRANSITIONS.get(current, [])
```

---

#### ⚠️ **2.3.2 Processing History Aggregation**

**Missing**: No service to aggregate processing history for analytics.

**Recommendation**: Add analytics service:
```python
@staticmethod
def get_processing_metrics(
    date_from: datetime = None,
    date_to: datetime = None,
    processing_type: str = None
) -> Dict:
    """Get aggregated processing metrics."""
    # Average processing time
    # Success/failure rates
    # Cost per document
    # Most common errors
```

---

### 2.4 Integration Gaps

#### ✅ **2.4.1 Document Handling Task Integration** - **VERIFIED**

**Status**: ✅ **FULLY INTEGRATED** - ProcessingJob creation and tracking is properly implemented in `document_handling/tasks/document_tasks.py`.

---

## 3. Cross-Directory Issues

### 3.1 Missing Integration Points

#### ❌ **3.1.1 Rule Version → Document Processing**

**Issue**: When rule versions change, should trigger document re-validation.

**Recommendation**: Add signal handler:
```python
@receiver(post_save, sender=VisaRuleVersion)
def handle_rule_version_published(sender, instance, created, **kwargs):
    if instance.is_published and not created:
        # Trigger document re-validation for affected cases
        # Queue processing jobs for documents that need re-checking
        pass
```

---

#### ❌ **3.1.2 Document Processing → Rule Engine**

**Issue**: Document validation should use rule engine for requirement matching.

**Current State**: Need to verify if document requirement matching uses rule engine.

**Action Required**: Review `DocumentRequirementMatchingService` integration.

---

## 4. Security Concerns

### 4.1 Input Validation

#### ⚠️ **4.1.1 JSON Logic Expression Injection**

**Risk**: **MEDIUM** - Malicious JSON Logic expressions could cause issues.

**Mitigation**: 
- Validate expression structure
- Sanitize variable names
- Limit expression complexity
- Test expressions in sandbox

---

### 4.2 Access Control

#### ✅ **4.2.1 Admin Endpoints**

**Status**: Properly protected with `IsAdminOrStaff` permission.

---

## 5. Performance Recommendations

### 5.1 Database Optimization

1. **Add Missing Indexes**:
   - `VisaRequirement(rule_version, requirement_code)` - for requirement lookups
   - `ProcessingJob(status, priority, created_at)` - already exists ✅
   - `ProcessingHistory(case_document, created_at)` - already exists ✅

2. **Query Optimization**:
   - Use `select_related()` for foreign keys (already done ✅)
   - Use `prefetch_related()` for reverse foreign keys where needed
   - Add database query logging in development

---

### 5.2 Caching Strategy

1. **Cache Active Rule Versions** (as mentioned in 1.4.1)
2. **Cache Document Requirements** per rule version
3. **Cache Processing Job Statistics** (refresh every 5 minutes)

---

## 6. Testing Recommendations

### 6.1 Unit Tests Needed

**rules_knowledge**:
- Rule version overlap detection
- JSON Logic validation
- Requirement evaluation edge cases
- Rule publishing workflow
- Soft delete with references

**document_processing**:
- Processing job state transitions
- Retry logic
- Timeout detection
- Cost calculation

---

### 6.2 Integration Tests Needed

- Rule version creation → document re-validation
- Processing job creation → Celery task execution
- Processing history logging
- Admin bulk operations

---

### 6.3 Performance Tests Needed

- Rule engine with 100+ requirements
- Document processing with large files
- Concurrent rule version updates
- Bulk operations with 1000+ records

---

## 7. Documentation Gaps

### 7.1 Missing Documentation

1. **Rule Version Lifecycle** - Document the complete lifecycle
2. **JSON Logic Expression Guide** - How to write valid expressions
3. **Processing Job Workflow** - Complete workflow documentation
4. **Error Handling Guide** - Common errors and resolutions
5. **Admin API Guide** - Complete admin API documentation

---

## 8. Critical Action Items (Priority Order)

### 🔴 **CRITICAL** (Must Fix Before Production)

1. **Add database constraint for rule version overlaps** (1.2.1)
2. **Implement soft delete for rule versions** (1.2.5)
3. **Add JSON Logic validation in repository layer** (1.2.2)
4. **Add requirement_code uniqueness constraint** (1.2.3) - **VERIFIED MISSING**: No unique_together constraint in VisaRequirement.Meta

### 🟡 **HIGH** (Should Fix Soon)

6. **Add rule version change history/audit trail** (1.2.6)
7. **Add processing job retry logic** (2.2.2)
8. **Add rule version effective date validation** (1.2.4)
9. **Add processing job timeout handling** (2.2.4)
10. **Add rule version conflict detection service** (1.3.1)

### 🟢 **MEDIUM** (Nice to Have)

11. **Add caching for active rule versions** (1.4.1)
12. **Add rule version comparison/diff** (1.3.2)
13. **Add processing job cost tracking** (2.2.5)
14. **Add processing history aggregation** (2.3.2)
15. **Add comprehensive unit tests** (6.1)

---

## 9. Advanced Design Recommendations

### 9.1 Event-Driven Architecture

**Recommendation**: Consider event-driven patterns for rule changes:
```python
# When rule version published:
event_bus.publish('rule_version.published', {
    'rule_version_id': str(version.id),
    'visa_type_id': str(version.visa_type.id),
    'effective_from': version.effective_from.isoformat()
})

# Listeners:
# - Document re-validation service
# - Notification service
# - Analytics service
```

---

### 9.2 Rule Versioning Strategy

**Current**: Simple effective date range.

**Enhancement**: Consider semantic versioning:
```python
version_number = models.CharField(max_length=20)  # e.g., "1.2.3"
version_type = models.CharField(choices=[
    ('major', 'Major - Breaking changes'),
    ('minor', 'Minor - New requirements'),
    ('patch', 'Patch - Bug fixes')
])
```

---

### 9.3 Processing Job Queue Management

**Enhancement**: Add job queue management:
- Job prioritization
- Queue monitoring
- Dead letter queue for failed jobs
- Job scheduling (delayed processing)

---

## 10. Compliance & Audit

### 10.1 Audit Requirements

**Missing**: Comprehensive audit trail for:
- Rule version changes
- Requirement changes
- Processing job modifications
- Admin actions

**Recommendation**: Integrate with audit log service or add audit fields to models.

---

### 10.2 Data Retention

**Missing**: No data retention policies defined.

**Recommendation**: Add retention policies:
- Processing history: 90 days (detailed), 7 years (aggregated)
- Processing jobs: 30 days (failed), 7 days (completed)
- Rule versions: Never delete (soft delete only)

---

## 11. Summary

### Strengths ✅

1. **Excellent Architecture**: Proper separation of concerns, clean code structure
   - ✅ Repositories for write operations
   - ✅ Selectors for read operations
   - ✅ Services for business logic
   - ✅ Views call services only
   - ✅ No direct model access in services

2. **Comprehensive Admin APIs**: Well-implemented admin functionality
   - ✅ All models have admin endpoints
   - ✅ Advanced filtering capabilities
   - ✅ Bulk operations support
   - ✅ Statistics and analytics endpoints
   - ✅ Proper permission classes

3. **Good Model Design**: Proper indexes, relationships, constraints
   - ✅ Appropriate indexes for common queries
   - ✅ Foreign key relationships properly defined
   - ✅ Unique constraints where needed (mostly)

4. **Error Handling**: Consistent error handling patterns
   - ✅ Try-except blocks in services
   - ✅ Proper logging
   - ✅ Graceful error returns

5. **Integration Points**: Well-integrated
   - ✅ ProcessingJob integration with document_handling ✅
   - ✅ Conditional document requirement evaluation ✅
   - ✅ Rule engine integration with document matching ✅

6. **Rule Engine**: Comprehensive implementation
   - ✅ Stateless, scalable design
   - ✅ Comprehensive edge case handling
   - ✅ JSON Logic evaluation
   - ✅ Missing variable detection

7. **Rule Publishing**: Complete workflow
   - ✅ Automated publishing from parsed rules
   - ✅ Manual rule creation
   - ✅ Version closing logic
   - ✅ User notifications

### Critical Gaps ❌

1. **Database Constraints**: Missing constraints for data integrity
   - ❌ No constraint preventing rule version overlaps
   - ❌ No unique constraint on (rule_version, requirement_code)
   - ❌ No check constraint for effective date ranges

2. **Validation**: Missing validation in repository layer
   - ❌ JSON Logic expressions not validated before saving
   - ❌ No validation for effective date ranges
   - ❌ No validation for past effective dates on published rules

3. **Soft Delete**: Hard deletes can break data integrity
   - ❌ Rule versions hard deleted (can break eligibility results)
   - ❌ No reference checking before deletion
   - ❌ No audit trail of deletions

4. **Audit Trail**: Missing user tracking
   - ❌ No created_by/updated_by fields on rule versions
   - ❌ No published_by/published_at tracking
   - ❌ Limited audit trail for rule changes

5. **Processing Job Features**: Some features missing
   - ❌ No automatic retry logic
   - ❌ No timeout detection/handling
   - ❌ No structured cost tracking

### Recommendations 📋

1. **Immediate (Critical)**: 
   - Add database constraints (overlaps, uniqueness)
   - Implement soft delete for rule versions
   - Add JSON Logic validation in repository layer
   - Add requirement_code uniqueness constraint

2. **Short-term (High Priority)**:
   - Add rule version change history/audit trail
   - Add processing job retry logic
   - Add rule version effective date validation
   - Add processing job timeout handling
   - Add rule version conflict detection service

3. **Medium-term (Enhancements)**:
   - Add caching for active rule versions
   - Add rule version comparison/diff
   - Add processing job cost tracking
   - Add processing history aggregation
   - Add comprehensive unit tests

4. **Long-term (Advanced Features)**:
   - Event-driven architecture for rule changes
   - Semantic versioning for rule versions
   - Advanced processing job queue management
   - Comprehensive audit logging system

---

**Next Steps**: Prioritize critical action items and create implementation tickets.

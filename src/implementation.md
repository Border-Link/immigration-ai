# Immigration Intelligence Platform
## Complete System Design & Implementation Plan

**Version:** 1.0  
**Date:** 2024  
**Status:** Developer-Ready Implementation Plan

---

# Table of Contents

1. [Executive Overview](#section-1-executive-overview)
2. [Architecture Overview](#section-2-architecture-overview)
3. [Database Design & Mapping to Workflows](#section-3-database-design--mapping-to-workflows)
4. [API Specification & Mapping](#section-4-api-specification--mapping)
5. [Data Ingestion & Scraper Flow](#section-5-data-ingestion--scraper-flow)
6. [AI Reasoning & Rule Engine Flow](#section-6-ai-reasoning--rule-engine-flow)
7. [Human-in-Loop Validation Flow](#section-7-human-in-loop-validation-flow)
8. [Document Upload & Checking](#section-8-document-upload--checking)
9. [Security, GDPR, and Compliance](#section-9-security-gdpr-and-compliance)
10. [Step-by-Step Implementation Plan](#section-10-step-by-step-implementation-plan)
11. [Example Code Snippets / Pseudocode](#section-11-example-code-snippets--pseudocode)
12. [Phased Roadmap](#section-12-phased-roadmap)
13. [Developer Notes](#section-13-developer-notes)

---

# Section 1: Executive Overview

## 1.1 System Purpose

The Immigration Intelligence Platform is a compliance-aware AI system that reduces failed visa applications and 
accelerates skilled migration through explainable AI and human-in-the-loop workflows. The platform provides decision 
support, document preparation, and information interpretation—not legal advice—for immigration applicants, particularly 
targeting UK immigration routes initially.

## 1.2 Value Proposition

### For Users (Applicants)
- **Reduced Application Failures**: Proactive identification of eligibility gaps and missing documents before submission
- **Time Savings**: Automated eligibility checks and document validation reduce manual research time
- **Transparency**: Every recommendation is traceable to official government sources with citations
- **Confidence**: Clear confidence scores and risk indicators help users make informed decisions

### For Business
- **Scalable Revenue Model**: Pay-per-case (£30-£150), subscription (universities/employers), white-label SaaS
- **Regulatory Compliance**: Built-in OISC boundary compliance, GDPR-ready, audit trails
- **Market Expansion**: Architecture supports multi-country expansion (UK → Canada → Australia → EU)
- **Infrastructure Positioning**: API-driven, embeddable in universities, employers, NGOs

## 1.3 Key System Principles

1. **Explainable AI**: Every AI output includes source-linked citations, confidence scores, and reasoning traces
2. **Hybrid Architecture**: Combines deterministic rule engines (for hard requirements) with AI reasoning (for nuanced interpretation)
3. **Human-in-Loop**: Automatic escalation to qualified reviewers when AI confidence is low or rules conflict
4. **Immigration-as-Infrastructure**: White-labelable, API-driven platform, not just a consumer app
5. **Full Auditability**: Every decision, rule change, and human override is logged and traceable
6. **Versioned Rules**: Immigration law changes are tracked with full temporal accuracy
7. **GDPR-Compliant**: Data minimization, right-to-erasure, explicit consent flows

---

# Section 2: Architecture Overview

## 2.1 System Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Applicant  │  │   Reviewer   │  │    Admin     │         │
│  │    Portal    │  │   Console    │  │   Console    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Authentication | Rate Limiting | Request Routing     │     │
│  └──────────────────────────────────────────────────────┘     │
└───────────────────────────┬───────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼─────────┐ ┌────▼─────┐ ┌─────────▼─────────┐
│   CASE SERVICE    │ │  RULE    │ │  DOCUMENT SERVICE  │
│                   │ │  ENGINE  │ │                    │
│ - Case Management │ │          │ │ - Upload/Storage   │
│ - Fact Collection │ │ - JSON   │ │ - OCR/Classification│
│ - Status Tracking │ │  Logic   │ │ - Validation       │
│                   │ │  Eval    │ │                    │
└─────────┬─────────┘ └────┬─────┘ └─────────┬─────────┘
          │                │                 │
          └────────────────┼─────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    AI REASONING SERVICE                       │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  RAG Orchestrator                                    │     │
│  │  - pgvector Retrieval                                 │     │
│  │  - LLM Prompt Construction                           │     │
│  │  - Citation Extraction                               │     │
│  │  - Confidence Scoring                               │     │
│  └──────────────────────────────────────────────────────┘     │
└──────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼─────────┐ ┌────▼─────┐ ┌─────────▼─────────┐
│   PGVECTOR        │ │   LLM    │ │  CITATION TRACKER  │
│   (PostgreSQL     │ │  SERVICE │ │                    │
│    Extension)     │ │ (OpenAI/ │ │ - Source Mapping   │
│                   │ │ Anthropic)│ │ - Excerpt Storage  │
│ - Document Chunks │ │          │ │                    │
│ - Embeddings      │ │ - GPT-4  │ │                    │
│ - Metadata        │ │ - Claude │ │                    │
└───────────────────┘ └──────────┘ └────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              DATA INGESTION SERVICE (IRIMS)                   │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Scheduler → Fetcher → Hasher → Diff Engine         │     │
│  │  → Rule Parser (AI) → Validation Queue → Publisher  │     │
│  └──────────────────────────────────────────────────────┘     │
│  Sources: gov.uk, Immigration Rules, Policy PDFs              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    DATABASE LAYER (PostgreSQL)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Users &    │  │   Cases &    │  │   Rules &    │       │
│  │   Profiles   │  │    Facts     │  │  Versions    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Documents  │  │   AI Logs &  │  │   Reviews &  │       │
│  │   & Checks   │  │  Citations   │  │  Overrides   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Ingestion  │  │   Audit      │  │   Payments   │       │
│  │   Pipeline   │  │    Logs      │  │   (Optional) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└───────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    OBJECT STORAGE (S3)                        │
│  - Raw source documents (PDFs, HTML)                          │
│  - User-uploaded documents                                    │
│  - Encrypted at rest                                          │
└───────────────────────────────────────────────────────────────┘
```

## 2.2 Service Boundaries & Dependencies

### Core Services

1. **Case Service**
   - Manages user cases, fact collection, status transitions
   - Depends on: Database, Rule Engine
   - Publishes events: `case.created`, `case.facts_updated`, `case.status_changed`

### Immigration Cases Service Architecture

The Immigration Cases module follows a strict layered architecture pattern:

**Layer Structure:**
- **Views** (`views/`): API endpoints that handle HTTP requests/responses
  - Views call services only, no direct model access
  - All views use serializers for input validation and output formatting
  - Proper error handling with consistent response format
  - Admin views separated in `views/admin/` directory
  
- **Services** (`services/`): Business logic layer
  - Services call selectors (read) and repositories (write)
  - No direct ORM access in services
  - All business logic encapsulated here
  - Audit logging integrated for all critical operations (create, update, delete)
  
- **Selectors** (`selectors/`): Read-only data access layer
  - All database read operations
  - Optimized queries with proper prefetching
  - Advanced filtering methods for admin functionality
  - No state mutations
  
- **Repositories** (`repositories/`): Write-only data access layer
  - All database write operations (create, update, delete)
  - Transaction management with `transaction.atomic()`
  - Proper validation and error handling

**Key Features:**
- **Status Lifecycle Management**: Case status transitions (draft → evaluated → awaiting_review → reviewed → closed)
  - Status transitions validated via `CaseStatusTransitionValidator` helper
  - Invalid transitions rejected with clear error messages
  - Prerequisites validated before status changes (e.g., facts required for 'evaluated')
- **Optimistic Locking**: Case model includes `version` field to prevent concurrent modification conflicts
  - Version checked on updates, conflicts return 409 status
  - Atomic version increments using `F('version') + 1`
- **Status History Tracking**: Complete audit trail via `CaseStatusHistory` model
  - All status changes tracked with previous/new status, changed_by, reason, metadata
  - Admin API to view status history for any case
- **Soft Delete**: Cases can be soft-deleted (is_deleted flag) instead of hard delete
  - Soft-deleted cases excluded from normal queries
  - Restore functionality available
  - Hard delete still available for admin operations
- **Case Fact Management**: Flexible key-value store for case data with append-only design for auditability
  - Business rule validation for fact keys and values
  - Type checking for fact values based on fact key
  - Whitelist of allowed fact keys (extensible)
- **Pagination**: All list endpoints support pagination
  - `page` and `page_size` query parameters
  - Pagination metadata included in responses
  - Default page size: 20, max: 100
- **Caching**: Frequently accessed data cached for performance
  - Case by ID cached (1 hour)
  - User's cases cached (10 minutes)
  - Case facts by case cached (10 minutes)
  - Cache invalidation on updates/deletes
- **Audit Logging**: All critical operations logged via `AuditLogService`
- **Transaction Management**: All write operations wrapped in transactions for atomicity
- **Advanced Filtering**: Comprehensive filtering capabilities for admin operations
- **Database Constraints**: CheckConstraint ensures valid status values at database level

**Data Flow:**
1. API Request → View (validates input via serializer)
2. View → Service (business logic)
3. Service → Selector (read, with caching) or Repository (write, with validation)
4. Repository → Database (with transaction, optimistic locking, status history tracking)
5. Repository → Cache Invalidation (on updates/deletes)
6. Service → Audit Logging (for critical operations)
7. View → Response (serialized output with pagination metadata if applicable)

**Error Handling:**
- Serializers validate input and return structured errors with field-level details
- Services catch exceptions and log errors with context
- Views return consistent error responses with specific messages
- Validation errors (status transitions, optimistic locking) return 409 Conflict
- Audit logging failures don't break operations (graceful degradation)

**Admin Control Flows:**
- All admin operations exposed via REST APIs (no Django admin)
- Permission-based access control (`IsAdminOrStaff`)
- Bulk operations supported for efficiency
- Advanced filtering and analytics available
- Statistics endpoint for system-wide metrics
- Status history viewing for audit trails

2. **Rule Engine Service**
   - Evaluates deterministic eligibility rules using JSON Logic
   - Depends on: Database (visa_requirements, case_facts)
   - Stateless, horizontally scalable

3. **AI Reasoning Service**
   - Orchestrates RAG retrieval, LLM calls, citation extraction
   - Depends on: pgvector (PostgreSQL), LLM API, Database
   - Handles: Low-confidence escalation, citation tracking

4. **Document Service**
   - Handles uploads, OCR, classification, validation
   - Depends on: Object Storage, OCR Service, Database
   - Publishes events: `document.uploaded`, `document.verified`, `document.rejected`

5. **Ingestion Service (IRIMS)**
   - Independent service for scraping, change detection, rule parsing
   - Depends on: Database, LLM API (for parsing), Object Storage
   - Publishes events: `rule.change_detected`, `rule.published`

6. **Review Service**
   - Manages human review workflows, overrides, reviewer assignments
   - Depends on: Database, Notification Service
   - Publishes events: `review.assigned`, `review.completed`, `override.created`

### Human Review Service Architecture

The Human Review module follows a strict layered architecture pattern:

**Layer Structure:**
- **Views** (`views/`): API endpoints that handle HTTP requests/responses
  - Views call services only, no direct model access
  - All views use serializers for input validation and output formatting
  - Proper error handling with consistent response format
  
- **Services** (`services/`): Business logic layer
  - Services call selectors (read) and repositories (write)
  - No direct ORM access in services
  - All business logic encapsulated here
  - Audit logging integrated for all critical operations
  
- **Selectors** (`selectors/`): Read-only data access layer
  - All database read operations
  - Optimized queries with proper prefetching
  - No state mutations
  
- **Repositories** (`repositories/`): Write-only data access layer
  - All database write operations (create, update, delete)
  - Transaction management with `transaction.atomic()`
  - Optimistic locking support (version field)
  - Status history tracking integrated

**Key Features:**
- **Optimistic Locking**: Review model includes `version` field to prevent concurrent modification conflicts
- **Status Transition Validation**: All status changes validated via `ReviewStatusTransitionValidator`
- **Status History Tracking**: Complete audit trail via `ReviewStatusHistory` model
- **Audit Logging**: All critical operations logged via `AuditLogService`
- **Transaction Management**: Multi-step operations wrapped in transactions for atomicity

**Data Flow:**
1. API Request → View (validates input via serializer)
2. View → Service (business logic)
3. Service → Selector (read) or Repository (write)
4. Repository → Database (with transaction and optimistic locking)
5. Service → Audit Logging (for critical operations)
6. View → Response (serialized output)

**Error Handling:**
- Serializers validate input and return structured errors
- Services catch exceptions and log errors
- Views return consistent error responses
- Audit logging failures don't break operations (graceful degradation)

**Admin Control Flows:**
- All admin operations exposed via REST APIs (no Django admin)
- Permission-based access control (`IsAdminOrStaff`)
- Bulk operations supported for efficiency
- Advanced filtering and analytics available

### Data Flow Patterns

- **Synchronous**: User API calls → Case Service → Rule Engine → Response
- **Asynchronous**: Ingestion Service → Rule Parser → Validation Queue → Admin Notification
- **Event-Driven**: Case status changes trigger eligibility checks, document validation triggers AI checks

---

# Section 3: Database Design & Mapping to Workflows

## 3.1 Complete ERD with Relationships

### Entity Groups

```
USERS & ACCESS
├── users (id, email, password_hash, role, is_active, created_at, updated_at)
└── user_profiles (user_id PK, first_name, last_name, nationality, date_of_birth, created_at)

IMMIGRATION CASES
├── cases (id, user_id FK, jurisdiction, status, created_at, updated_at)
└── case_facts (id, case_id FK, fact_key, fact_value JSONB, source, created_at)

RULES & KNOWLEDGE
├── visa_types (id, jurisdiction, code, name, description)
├── visa_rule_versions (id, visa_type_id FK, effective_from, effective_to, source_document_version_id FK)
├── visa_requirements (id, rule_version_id FK, requirement_code, description, condition_expression JSONB)
├── visa_document_requirements (id, rule_version_id FK, document_type_id FK, mandatory)
└── document_types (id, code, name, description)

DATA INGESTION
├── data_sources (id, name, base_url, jurisdiction, is_active)
├── source_documents (id, data_source_id FK, source_url, fetched_at)
├── document_versions (id, source_document_id FK, content_hash, raw_text, extracted_at)
├── document_diffs (id, old_version_id FK, new_version_id FK, diff_text, created_at)
├── parsed_rules (id, document_version_id FK, visa_code, rule_type, extracted_logic, confidence_score, status)
└── rule_validation_tasks (id, parsed_rule_id FK, assigned_to FK, status, reviewer_notes, reviewed_at)

AI & DECISIONS
├── eligibility_results (id, case_id FK, visa_type_id FK, rule_version_id FK, outcome, confidence, created_at)
├── ai_reasoning_logs (id, case_id FK, prompt, response, model_name, created_at)
└── ai_citations (id, reasoning_log_id FK, document_version_id FK, excerpt)

DOCUMENT HANDLING
├── case_documents (id, case_id FK, document_type_id FK, file_path, uploaded_at)
└── document_checks (id, case_document_id FK, check_type, result, details, created_at)

HUMAN REVIEW
├── reviews (id, case_id FK, reviewer_id FK, status, created_at)
├── review_notes (id, review_id FK, note, created_at)
└── decision_overrides (id, case_id FK, original_result_id FK, overridden_outcome, reason, reviewer_id FK, created_at)

COMPLIANCE
└── audit_logs (id, actor_id, action, entity_type, entity_id, metadata JSONB, created_at)

OPTIONAL (MVP+)
└── payments (id, case_id FK, amount, currency, status, payment_provider, created_at)
```

### Key Relationships

1. **users (1) ────< cases (many)**: One user can have multiple immigration cases
2. **cases (1) ────< case_facts (many)**: Append-only facts for auditability
3. **visa_types (1) ────< visa_rule_versions (many) ────< visa_requirements (many)**: Versioned rules
4. **data_sources (1) ────< source_documents (many) ────< document_versions (many)**: Ingestion chain
5. **document_versions (1) ────< parsed_rules (many) ────< rule_validation_tasks (many)**: Human validation gate
6. **cases (1) ────< ai_reasoning_logs (many) ────< ai_citations (many)**: Explainability chain
7. **cases (1) ────< reviews (many) ────< review_notes (many)**: Human review workflow
8. **cases (1) ────< decision_overrides (many)**: Overrides layer on top of AI

## 3.2 Table Explanations & Workflow Mapping

### Users & Access Layer

**`users`**
- Purpose: Authentication and authorization
- Workflow: User registration → JWT token generation → Role-based access control
- Edge Cases: Inactive users cannot access cases, role changes require re-authentication

**`user_profiles`**
- Purpose: GDPR-friendly separation of PII from auth data
- Workflow: Profile creation → Consent tracking → Right-to-erasure support
- Edge Cases: Partial profiles allowed during onboarding, consent can be revoked

### Immigration Cases Layer

**`cases`**
- Purpose: Core entity representing one immigration journey
- Workflow: `draft` → `evaluated` → `awaiting_review` → `reviewed` → `closed`
- Edge Cases: Cases can be reopened, status transitions are logged, jurisdiction isolation prevents cross-country data leakage

**`case_facts`**
- Purpose: Flexible key-value store for case data (salary, age, nationality, etc.)
- Workflow: User submits facts → Rule engine reads → AI reasoning uses → Reviewer can override
- Edge Cases: 
  - Missing facts: Rule engine returns `missing_facts` list
  - Conflicting facts: Latest fact (by timestamp) wins, but history preserved
  - Source tracking: Distinguishes user-provided vs AI-derived vs reviewer-corrected

### Rules & Knowledge Layer

**`visa_types`**
- Purpose: Master list of visa routes (Skilled Worker, Student, Family, etc.)
- Workflow: Admin creates → Linked to rule versions → Used in eligibility checks
- Edge Cases: Inactive visa types hidden from users but preserved for historical cases

**`visa_rule_versions`**
- Purpose: Temporal versioning of immigration rules
- Workflow: Ingestion detects change → New version created → `effective_from` set → Previous version `effective_to` set
- Edge Cases:
  - Overlapping effective dates: System uses most recent version
  - Missing effective_to: Version is "current" until superseded
  - Rule conflicts: Human validation required before publishing

**`visa_requirements`**
- Purpose: Atomic eligibility requirements with machine-readable logic
- Workflow: Parsed from source → Validated by human → Stored as JSON Logic → Evaluated by rule engine
- Edge Cases:
  - Invalid JSON Logic: Validation task created, rule not published
  - Missing variables: Rule engine returns "cannot evaluate" → Escalates to human

**`visa_document_requirements`**
- Purpose: Document checklist per visa route and rule version
- Workflow: Derived from rule version → Shown to user → Validated against uploads
- Edge Cases: Conditional requirements (e.g., dependants require additional docs)

### Data Ingestion Layer

**`data_sources`**
- Purpose: Configuration for monitored sources (gov.uk pages, PDFs)
- Workflow: Admin configures → Scheduler fetches → Change detection → Versioning
- Edge Cases: Source becomes unavailable → System continues with last known version, alerts admin

**`source_documents`**
- Purpose: Raw fetched content (immutable)
- Workflow: Fetcher downloads → Hash computed → Stored → Never overwritten
- Edge Cases: Fetch failures → Retry with exponential backoff, max 3 attempts

**`document_versions`**
- Purpose: Versioned extracted text from source documents
- Workflow: Content hash changes → New version created → Diff computed → Rule parsing triggered
- Edge Cases: Hash collision (extremely rare) → Additional metadata comparison

**`document_diffs`**
- Purpose: Change detection and classification
- Workflow: Old vs new version compared → Diff stored → Change type classified → Admin notified
- Edge Cases: Large diffs → Summarized, full diff available on demand

**`parsed_rules`**
- Purpose: AI-extracted rule candidates (staging area)
- Workflow: AI parses document version → Extracts logic → Confidence scored → Status = `pending` → Human validates
- Edge Cases:
  - Low confidence (<0.7): Auto-flagged for human review
  - Conflicting extractions: Multiple parsed_rules created, human resolves

**`rule_validation_tasks`**
- Purpose: Human-in-loop gate for rule publishing
- Workflow: Parsed rule created → Task assigned → Reviewer approves/rejects/edits → If approved, rule published
- Edge Cases: Reviewer timeout (7 days) → Escalates to senior reviewer

### AI & Decisions Layer

**`eligibility_results`**
- Purpose: Final eligibility outcome per visa route
- Workflow: Rule engine + AI reasoning → Outcome computed → Stored → Can be overridden
- Edge Cases:
  - Multiple results for same case: User sees all, can compare
  - Result conflicts with override: Override takes precedence, but original preserved

**`ai_reasoning_logs`**
- Purpose: Full AI reasoning trace for explainability
- Workflow: RAG retrieval → Prompt constructed → LLM called → Response stored → Citations extracted
- Edge Cases: LLM timeout → Retry with shorter context, if fails → Escalate to human

**`ai_citations`**
- Purpose: Source attribution for AI outputs
- Workflow: AI response parsed → Citations extracted → Linked to document_versions → Stored
- Edge Cases: Citation not found in pgvector → Warning logged, citation still stored with URL

### Document Handling Layer

**`case_documents`**
- Purpose: User-uploaded files
- Workflow: Upload → OCR → Classification → Validation → Status updated
- Edge Cases:
  - Unsupported file type: Rejected immediately
  - Corrupted file: Retry upload, max 3 attempts
  - Large file (>10MB): Compressed or chunked

**`document_checks`**
- Purpose: Automated and human validation results
- Workflow: Document uploaded → AI checks (OCR, classification) → Results stored → Human can override
- Edge Cases: Check fails → User notified, can resubmit

### Human Review Layer

**`reviews`**
- Purpose: Human review workflow management
- Workflow: Case flagged → Review created → Assigned to reviewer → Completed → Override possible
- Edge Cases: Reviewer unavailable → Reassigned, SLA tracking

**`review_notes`**
- Purpose: Reviewer annotations and reasoning
- Workflow: Reviewer adds notes → Stored → Visible to user and other reviewers
- Edge Cases: Sensitive information in notes → Redacted before user visibility

**`decision_overrides`**
- Purpose: Human authority over AI decisions
- Workflow: Reviewer disagrees with AI → Override created → Original preserved → New outcome applied
- Edge Cases: Multiple overrides → Latest wins, full history preserved

### Compliance Layer

**`audit_logs`**
- Purpose: Immutable audit trail
- Workflow: Every critical action → Logged → Never deleted → Queryable
- Edge Cases: High-volume logging → Partitioned by date, archived after 7 years

## 3.3 Indexes for Performance

```sql
-- Case lookups
CREATE INDEX idx_cases_user ON cases(user_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_case_facts_case ON case_facts(case_id);
CREATE INDEX idx_case_facts_key ON case_facts(fact_key);

-- Rule evaluation
CREATE INDEX idx_rule_versions_effective ON visa_rule_versions(visa_type_id, effective_from, effective_to);
CREATE INDEX idx_requirements_rule_version ON visa_requirements(rule_version_id);

-- AI reasoning
CREATE INDEX idx_eligibility_case ON eligibility_results(case_id);
CREATE INDEX idx_ai_reasoning_case ON ai_reasoning_logs(case_id);
CREATE INDEX idx_ai_citations_reasoning ON ai_citations(reasoning_log_id);

-- Document queries
CREATE INDEX idx_case_documents_case ON case_documents(case_id);
CREATE INDEX idx_document_checks_doc ON document_checks(case_document_id);

-- Ingestion
CREATE INDEX idx_document_versions_source ON document_versions(source_document_id);
CREATE INDEX idx_parsed_rules_status ON parsed_rules(status);
CREATE INDEX idx_validation_tasks_status ON rule_validation_tasks(status);

-- Audit
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id, created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
```

## 3.4 Versioning Strategies

### Rule Versioning
- **Effective Date Range**: `effective_from` and `effective_to` define temporal validity
- **Query Pattern**: `WHERE effective_from <= today AND (effective_to IS NULL OR effective_to >= today)`
- **Edge Case**: Overlapping versions → Most recent `effective_from` wins

### Document Versioning
- **Content Hash**: SHA-256 hash detects changes
- **Immutable Storage**: Never overwrite, always append new version
- **Diff Tracking**: Store diffs for change analysis

### Case Fact Versioning
- **Append-Only**: New facts appended, never updated
- **Source Tracking**: `source` field distinguishes user/AI/reviewer
- **Latest Wins**: Application logic selects most recent fact by `created_at`

---

# Section 4: API Specification & Mapping

## 4.1 Authentication & Authorization

### Authentication
- **Method**: JWT Bearer tokens
- **Endpoint**: `POST /api/v1/auth/login`
- **Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```
- **Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "user"
  }
}
```

### Authorization
- **Roles**: `user`, `reviewer`, `admin`
- **RBAC Mapping**:
  - `user`: Own cases only
  - `reviewer`: Assigned reviews + own cases
  - `admin`: All cases + rule management + ingestion control

## 4.2 Case Management APIs

### 4.2.1 Create Case
**Endpoint**: `POST /api/v1/cases`  
**Auth**: Required (user role)  
**Request**:
```json
{
  "jurisdiction": "UK"
}
```
**Response**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "created_at": "2024-01-15T10:00:00Z"
}
```
**DB Mapping**:
- Inserts into `cases` table
- Sets `user_id` from JWT token
- Initial status: `draft`
- **Edge Cases**:
  - Invalid jurisdiction → 400 Bad Request
  - User already has 10 active cases → 429 Too Many Requests (rate limit)

### 4.2.2 Submit Case Facts
**Endpoint**: `POST /api/v1/cases/{case_id}/facts`  
**Auth**: Required (user role, own case only)  
**Request**:
```json
{
  "facts": {
    "age": 29,
    "nationality": "NG",
    "salary": 42000,
    "has_sponsor": true,
    "sponsor_name": "Tech Corp Ltd",
    "job_title": "Software Engineer",
    "dependants": 0
  }
}
```
**Response**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "facts_submitted": 7,
  "status": "draft"
}
```
**DB Mapping**:
- Inserts multiple rows into `case_facts`
- Each fact: `case_id`, `fact_key`, `fact_value` (JSONB), `source='user'`
- **Edge Cases**:
  - Invalid fact keys → 400 Bad Request (whitelist validation)
  - Missing required facts → 400 Bad Request (e.g., `nationality` required)
  - Case not found → 404 Not Found
  - Case not owned by user → 403 Forbidden

### 4.2.3 Get Case Details
**Endpoint**: `GET /api/v1/cases/{case_id}`  
**Auth**: Required (user: own case, reviewer: assigned, admin: all)  
**Response**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "evaluated",
  "jurisdiction": "UK",
  "facts": {
    "age": 29,
    "nationality": "NG",
    "salary": 42000
  },
  "eligibility_results": [
    {
      "visa_code": "SKILLED_WORKER",
      "outcome": "likely",
      "confidence": 0.92
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```
**DB Mapping**:
- Joins `cases`, `case_facts`, `eligibility_results`
- Aggregates facts into object
- **Edge Cases**:
  - Case deleted → 404 Not Found
  - Insufficient permissions → 403 Forbidden

### 4.2.4 Update Case Facts
**Endpoint**: `PATCH /api/v1/cases/{case_id}/facts`  
**Auth**: Required (user role, own case only, status = draft)  
**Request**:
```json
{
  "facts": {
    "salary": 45000
  }
}
```
**Response**: Same as Submit Case Facts  
**DB Mapping**:
- Appends new facts (append-only design)
- Previous facts preserved for audit
- **Edge Cases**:
  - Case status not `draft` → 400 Bad Request (cannot modify evaluated case)
  - Invalid fact values → 400 Bad Request

## 4.3 Eligibility & AI Reasoning APIs

### 4.3.1 Run Eligibility Check
**Endpoint**: `POST /api/v1/cases/{case_id}/eligibility`  
**Auth**: Required (user: own case, reviewer/admin: any)  
**Request**: (optional query params)
```json
{
  "visa_types": ["SKILLED_WORKER", "STUDENT"]  // Optional: filter specific visas
}
```
**Response**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "visa_code": "SKILLED_WORKER",
      "visa_name": "Skilled Worker Visa",
      "outcome": "likely",
      "confidence": 0.92,
      "rule_version_id": "660e8400-e29b-41d4-a716-446655440001",
      "rule_effective_from": "2024-01-01",
      "requirements_passed": 8,
      "requirements_total": 10,
      "missing_requirements": [
        {
          "requirement_code": "MIN_SALARY",
          "description": "Minimum salary threshold",
          "status": "passed"
        },
        {
          "requirement_code": "SPONSOR_LICENSE",
          "description": "Valid sponsor license",
          "status": "missing_fact"
        }
      ],
      "missing_documents": [
        "certificate_of_sponsorship",
        "bank_statement"
      ],
      "citations": [
        {
          "source_url": "https://www.gov.uk/skilled-worker-visa",
          "excerpt": "You must be paid at least £38,700 per year or the 'going rate' for your job, whichever is higher.",
          "document_version_id": "770e8400-e29b-41d4-a716-446655440002"
        }
      ],
      "reasoning_summary": "Your salary of £42,000 meets the minimum threshold. However, you need a valid Certificate of Sponsorship from your employer."
    }
  ],
  "requires_human_review": false,
  "low_confidence_flags": [],
  "generated_at": "2024-01-15T10:30:00Z"
}
```
**DB Mapping**:
1. Load `case_facts` for case_id
2. Load active `visa_rule_versions` (filter by jurisdiction, effective dates)
3. For each visa type:
   - Evaluate `visa_requirements` using rule engine (JSON Logic)
   - Call AI Reasoning Service for nuanced interpretation
   - Store `eligibility_results`
   - Store `ai_reasoning_logs`
   - Store `ai_citations`
4. Update `cases.status` to `evaluated`
5. **Edge Cases**:
   - Missing critical facts → Returns `missing_requirements` with `status: "missing_fact"`
   - AI service unavailable → Falls back to rule engine only, `confidence` reduced
   - Low confidence (<0.6) → `requires_human_review: true`, `low_confidence_flags: ["uncertain_interpretation"]`
   - Rule conflicts → Escalates to human, returns `pending_review` status

### 4.3.2 Get Eligibility Explanation
**Endpoint**: `GET /api/v1/cases/{case_id}/eligibility/{result_id}/explanation`  
**Auth**: Required  
**Response**:
```json
{
  "result_id": "880e8400-e29b-41d4-a716-446655440003",
  "full_reasoning": "Based on your case facts...",
  "ai_reasoning_log": {
    "prompt": "...",
    "response": "...",
    "model_name": "gpt-4",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "citations": [
    {
      "source_url": "https://www.gov.uk/...",
      "excerpt": "...",
      "document_version_id": "...",
      "page_number": 12
    }
  ],
  "rule_evaluation_details": [
    {
      "requirement_code": "MIN_SALARY",
      "expression": {">=": [{"var": "salary"}, 38700]},
      "evaluated_value": true,
      "explanation": "Salary £42,000 >= £38,700 threshold"
    }
  ]
}
```
**DB Mapping**:
- Joins `eligibility_results`, `ai_reasoning_logs`, `ai_citations`, `visa_requirements`
- **Edge Cases**: Result not found → 404

### 4.3.3 List AI Reasoning Logs (Reviewer Only)
**Endpoint**: `GET /api/v1/ai-decisions/ai-reasoning-logs/`  
**Auth**: Required (reviewer only - reviewers review AI decisions)  
**Query Params**:
- `case_id` (optional): Filter by case ID
- `model_name` (optional): Filter by model name (e.g., "gpt-4")

**Response**:
```json
{
  "message": "AI reasoning logs retrieved successfully.",
  "data": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440010",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "model_name": "gpt-4",
      "tokens_used": 1250,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```
**Use Cases**: Debugging, auditing, token usage tracking, AI quality analysis

### 4.3.4 Get AI Reasoning Log Detail (Reviewer Only)
**Endpoint**: `GET /api/v1/ai-decisions/ai-reasoning-logs/{log_id}/`  
**Auth**: Required (reviewer only - reviewers review AI decisions)  
**Response**:
```json
{
  "message": "AI reasoning log retrieved successfully.",
  "data": {
    "id": "aa0e8400-e29b-41d4-a716-446655440010",
    "case_id": "550e8400-e29b-41d4-a716-446655440000",
    "case_status": "evaluated",
    "prompt": "You are an immigration eligibility advisor...",
    "response": "Based on your case facts...",
    "model_name": "gpt-4",
    "tokens_used": 1250,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```
**Use Cases**: Full prompt/response inspection for debugging, compliance auditing

### 4.3.5 List AI Citations (Reviewer Only)
**Endpoint**: `GET /api/v1/ai-decisions/ai-citations/`  
**Auth**: Required (reviewer only - reviewers review AI decisions)  
**Query Params**:
- `reasoning_log_id` (optional): Filter by reasoning log ID
- `document_version_id` (optional): Filter by document version ID

**Response**:
```json
{
  "message": "AI citations retrieved successfully.",
  "data": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440011",
      "reasoning_log_id": "aa0e8400-e29b-41d4-a716-446655440010",
      "source_url": "https://www.gov.uk/skilled-worker-visa",
      "relevance_score": 0.92,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```
**Use Cases**: Citation quality analysis, source verification, debugging

### 4.3.6 Get AI Citation Detail (Reviewer Only)
**Endpoint**: `GET /api/v1/ai-decisions/ai-citations/{citation_id}/`  
**Auth**: Required (reviewer only - reviewers review AI decisions)  
**Response**:
```json
{
  "message": "AI citation retrieved successfully.",
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440011",
    "reasoning_log_id": "aa0e8400-e29b-41d4-a716-446655440010",
    "case_id": "550e8400-e29b-41d4-a716-446655440000",
    "document_version_id": "770e8400-e29b-41d4-a716-446655440002",
    "source_url": "https://www.gov.uk/skilled-worker-visa",
    "document_title": "Skilled Worker Visa - GOV.UK",
    "excerpt": "You must be paid at least £38,700 per year...",
    "relevance_score": 0.92,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```
**Use Cases**: Detailed citation inspection, source verification, quality assurance

**Note**: These endpoints (4.3.3-4.3.6) are **read-only** and restricted to reviewers (who review AI decisions) for:
- **Observability**: Monitor AI reasoning quality
- **Debugging**: Investigate AI decision issues
- **Compliance**: Audit AI outputs and citations
- **Analytics**: Track token usage and citation quality

### 4.3.7 Admin Management Endpoints (Staff/Superuser Only)
**Base Path**: `/api/v1/ai-decisions/admin/`

All admin endpoints use `IsAdminOrStaff` permission class (requires `is_staff=True` OR `is_superuser=True`).

#### Eligibility Results Admin
- `GET /api/v1/ai-decisions/admin/eligibility-results/` - List with advanced filtering (outcome, confidence, date range)
- `GET /api/v1/ai-decisions/admin/eligibility-results/<id>/` - Get detailed result
- `DELETE /api/v1/ai-decisions/admin/eligibility-results/<id>/` - Delete result (data cleanup)

#### AI Reasoning Logs Admin
- `GET /api/v1/ai-decisions/admin/ai-reasoning-logs/` - List with advanced filtering (model, tokens, date range)
- `GET /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/` - Get detailed log
- `DELETE /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/` - Delete log (data cleanup)

#### AI Citations Admin
- `GET /api/v1/ai-decisions/admin/ai-citations/` - List with advanced filtering (relevance, date range)
- `GET /api/v1/ai-decisions/admin/ai-citations/<id>/` - Get detailed citation
- `DELETE /api/v1/ai-decisions/admin/ai-citations/<id>/` - Delete citation (data cleanup)

**Use Cases**: Data management, cleanup, advanced analytics, system maintenance

**Note**: Django admin interface is disabled - all admin functionality is API-based.

## 4.4 Document Management APIs

### 4.4.1 Upload Document
**Endpoint**: `POST /api/v1/cases/{case_id}/documents`  
**Auth**: Required (user: own case)  
**Content-Type**: `multipart/form-data`  
**Request**:
```
file: [binary]
document_type: "passport"  // Optional: pre-classify
```
**Response**:
```json
{
  "document_id": "990e8400-e29b-41d4-a716-446655440004",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "detected_type": "passport",
  "classification_confidence": 0.95,
  "file_size": 2048576,
  "file_path": "s3://bucket/cases/550e8400/990e8400.pdf",
  "checks": [
    {
      "check_type": "ocr",
      "result": "pass",
      "details": "Text extracted successfully"
    },
    {
      "check_type": "classification",
      "result": "pass",
      "details": "Confirmed as passport"
    },
    {
      "check_type": "requirement_match",
      "result": "pass",
      "details": "Matches required document type"
    }
  ],
  "uploaded_at": "2024-01-15T11:00:00Z"
}
```
**DB Mapping**:
1. Store file in S3 (encrypted)
2. Insert `case_documents` row
3. Run OCR → Store text
4. Run classification AI → Update `document_type_id`
5. Run requirement matching → Insert `document_checks`
6. **Edge Cases**:
   - File too large (>10MB) → 413 Payload Too Large
   - Unsupported format → 400 Bad Request
   - OCR fails → `check.result: "fail"`, user can retry
   - Classification uncertain → `classification_confidence < 0.7` → Flag for human review

### 4.4.2 Get Document Status
**Endpoint**: `GET /api/v1/cases/{case_id}/documents`  
**Auth**: Required  
**Response**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "documents": [
    {
      "document_id": "990e8400-e29b-41d4-a716-446655440004",
      "document_type": "passport",
      "status": "accepted",
      "checks": [
        {"check_type": "ocr", "result": "pass"},
        {"check_type": "classification", "result": "pass"}
      ],
      "uploaded_at": "2024-01-15T11:00:00Z"
    }
  ],
  "required_documents": [
    {
      "document_type": "passport",
      "mandatory": true,
      "status": "provided"
    },
    {
      "document_type": "bank_statement",
      "mandatory": true,
      "status": "missing"
    },
    {
      "document_type": "certificate_of_sponsorship",
      "mandatory": true,
      "status": "missing"
    }
  ],
  "completion_percentage": 33
}
```
**DB Mapping**:
- Joins `case_documents`, `document_types`, `visa_document_requirements`, `document_checks`
- Computes missing documents by comparing requirements vs uploads
- **Edge Cases**: No documents uploaded → Returns empty array, 100% missing

### 4.4.3 Delete Document
**Endpoint**: `DELETE /api/v1/cases/{case_id}/documents/{document_id}`  
**Auth**: Required (user: own case, status = draft)  
**Response**: 204 No Content  
**DB Mapping**:
- Soft delete: Set `deleted_at` timestamp (or hard delete if GDPR request)
- Delete from S3
- **Edge Cases**: Case not in `draft` status → 400 Bad Request

## 4.5 Human Review APIs

### 4.5.1 Submit for Review
**Endpoint**: `POST /api/v1/cases/{case_id}/review`  
**Auth**: Required (user: own case)  
**Request**:
```json
{
  "note": "Please verify sponsor eligibility",
  "priority": "normal"  // Optional: "normal", "urgent"
}
```
**Response**:
```json
{
  "review_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "awaiting_review",
  "estimated_completion_days": 2,
  "created_at": "2024-01-15T12:00:00Z"
}
```
**DB Mapping**:
- Insert `reviews` row (status = `in_progress` initially, then queued)
- Insert `review_notes` with user note
- Update `cases.status` to `awaiting_review`
- Assign to available reviewer (round-robin or workload-based)
- **Edge Cases**:
  - No reviewers available → Status = `awaiting_review`, SLA extended
  - Case already under review → 400 Bad Request

### 4.5.2 Get Review Queue (Admin/Reviewer)
**Endpoint**: `GET /api/v1/admin/reviews`  
**Auth**: Required (reviewer/admin role)  
**Query Params**: `?status=pending&assigned_to={reviewer_id}`  
**Response**:
```json
{
  "reviews": [
    {
      "review_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "assigned_to": "bb0e8400-e29b-41d4-a716-446655440006",
      "status": "in_progress",
      "risk_flags": ["salary_edge_case", "low_confidence"],
      "ai_confidence": 0.61,
      "user_note": "Please verify sponsor eligibility",
      "created_at": "2024-01-15T12:00:00Z",
      "sla_deadline": "2024-01-17T12:00:00Z"
    }
  ],
  "total_pending": 15,
  "total_in_progress": 3
}
```
**DB Mapping**:
- Joins `reviews`, `cases`, `eligibility_results`, `users`
- Filters by status and assigned reviewer
- **Edge Cases**: No reviews → Empty array

### 4.5.3 Reviewer Override Decision
**Endpoint**: `POST /api/v1/reviews/{review_id}/decision`  
**Auth**: Required (reviewer/admin, assigned review)  
**Request**:
```json
{
  "outcome": "possible",
  "reason": "Salary acceptable due to shortage occupation exception",
  "notes": "Verified sponsor license, exception applies per Appendix K"
}
```
**Response**:
```json
{
  "override_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "review_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "original_outcome": "unlikely",
  "overridden_outcome": "possible",
  "reason": "Salary acceptable due to shortage occupation exception",
  "reviewer_id": "bb0e8400-e29b-41d4-a716-446655440006",
  "created_at": "2024-01-15T14:00:00Z"
}
```
**DB Mapping**:
1. Insert `decision_overrides` row
2. Insert `review_notes` with reviewer notes
3. Update `reviews.status` to `completed`
4. Update `cases.status` to `reviewed`
5. **Edge Cases**:
   - Review not assigned to reviewer → 403 Forbidden
   - Invalid outcome value → 400 Bad Request

## 4.6 Admin APIs

### 4.6.1 Manage Rule Validation Tasks
**Endpoint**: `GET /api/v1/admin/rule-validation-tasks`  
**Auth**: Required (admin role)  
**Query Params**: `?status=pending&assigned_to={user_id}`  
**Response**:
```json
{
  "tasks": [
    {
      "task_id": "dd0e8400-e29b-41d4-a716-446655440008",
      "parsed_rule_id": "ee0e8400-e29b-41d4-a716-446655440009",
      "assigned_to": "ff0e8400-e29b-41d4-a716-446655440010",
      "status": "open",
      "parsed_rule": {
        "visa_code": "SKILLED_WORKER",
        "rule_type": "eligibility",
        "extracted_logic": {"min_salary": 38700},
        "confidence_score": 0.85,
        "source_document": {
          "url": "https://www.gov.uk/...",
          "version_id": "770e8400-e29b-41d4-a716-446655440002"
        }
      },
      "diff_summary": "Salary threshold changed from £38,000 to £38,700",
      "created_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

**Endpoint**: `POST /api/v1/admin/rule-validation-tasks/{task_id}/approve`  
**Auth**: Required (admin role)  
**Request**:
```json
{
  "reviewer_notes": "Verified against official source, threshold correct",
  "edits": {
    "condition_expression": {
      ">=": [{"var": "salary"}, 38700]
    }
  }
}
```
**Response**: 200 OK  
**DB Mapping**:
- Updates `rule_validation_tasks.status` to `approved`
- If approved, promotes to `visa_rule_versions` and `visa_requirements`
- Sets `effective_to` on previous version
- **Edge Cases**: Task already approved → 400 Bad Request

### 4.6.2 Manage Data Sources
**Endpoint**: `GET /api/v1/admin/data-sources`  
**Endpoint**: `POST /api/v1/admin/data-sources`  
**Endpoint**: `PUT /api/v1/admin/data-sources/{source_id}`  
**Auth**: Required (admin role)  
**Standard CRUD operations for ingestion configuration**

## 4.7 Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "Case with ID 550e8400... not found",
    "details": {
      "case_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success, no response body
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `413 Payload Too Large`: File too large
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Dependent service down

### Edge Case Error Codes
- `MISSING_REQUIRED_FACTS`: Case facts incomplete
- `RULE_EVALUATION_FAILED`: Rule engine error
- `AI_SERVICE_UNAVAILABLE`: LLM service down (fallback to rule engine)
- `DOCUMENT_PROCESSING_FAILED`: OCR/classification failed
- `REVIEWER_UNAVAILABLE`: No reviewers available
- `RULE_CONFLICT_DETECTED`: Conflicting rule versions

---

# Section 5: Data Ingestion & Scraper Flow

## 5.1 Ingestion Service Architecture (IRIMS)

### Service Components

1. **Scheduler** (Airflow/Celery Beat)
   - Triggers periodic fetches based on `data_sources.crawl_frequency`
   - Handles retries and failure notifications

2. **Fetcher**
   - HTTP client for HTML pages
   - PDF downloader
   - Respects `robots.txt`
   - User-agent: "ImmigrationIntelligenceBot/1.0"

3. **Hasher**
   - Computes SHA-256 hash of content
   - Compares with last known hash
   - Detects changes

4. **Version Store**
   - Creates `source_documents` entry
   - Creates `document_versions` entry
   - Never overwrites

5. **Diff Engine**
   - Compares old vs new text
   - Classifies change type (minor_text, requirement_change, fee_change, etc.)
   - Stores in `document_diffs`

6. **Rule Parser (AI-assisted)**
   - Calls LLM to extract structured rules from text
   - Outputs JSON Logic expressions
   - Stores in `parsed_rules` with confidence score

7. **Validation Queue**
   - Creates `rule_validation_tasks`
   - Assigns to reviewers
   - Notifies admins

8. **Publisher**
   - Promotes approved rules to `visa_rule_versions`
   - Updates pgvector (PostgreSQL)
   - Closes previous rule versions

## 5.2 Scraping Strategy

### Source Types

**HTML Pages (gov.uk)**
- Strategy: Static HTML parsing (avoid JS-heavy pages)
- Tools: `requests` + `BeautifulSoup`
- Extraction: Main content, ignore navigation/footers
- Change Detection: Hash entire content, or hash main content region

**PDF Documents**
- Strategy: Download and extract text
- Tools: `pdfminer.six` or `PyPDF2`
- Extraction: Full text, preserve page numbers for citations
- Change Detection: Hash extracted text

**API Endpoints** (if available)
- Strategy: JSON/XML parsing
- Tools: `requests` + JSON parser
- Extraction: Structured data
- Change Detection: Hash JSON payload

### Respectful Scraping

- **Rate Limiting**: Max 1 request per 2 seconds per domain
- **robots.txt**: Always check and respect
- **User-Agent**: Identifiable, contact info in user-agent string
- **Error Handling**: Exponential backoff on failures
- **Monitoring**: Alert on repeated failures

## 5.3 Change Detection Logic

### Flow Diagram

```
Fetch Source
    ↓
Compute Hash (SHA-256)
    ↓
Query Last Hash from document_versions
    ↓
Hash Match?
    ├─ Yes → No Action (skip)
    └─ No → Change Detected
            ↓
        Store New source_documents
            ↓
        Store New document_versions
            ↓
        Compute Diff (old vs new)
            ↓
        Store document_diffs
            ↓
        Classify Change Type
            ↓
        Trigger Rule Parsing
```

### Change Classification

**Step-by-Step Implementation**:

1. **Analyze Diff Text**:
   - Search for numeric patterns (currency symbols like £, percentages)
   - Search for date/time patterns (days, weeks, months)
   - Search for keywords related to requirements, fees, or processing times

2. **Classification Logic**:
   - If numeric values found AND keywords like "salary" or "threshold" present → Classify as `requirement_change`
   - If numeric values found AND keyword "fee" present → Classify as `fee_change`
   - If date/time patterns found → Classify as `processing_time_change`
   - If none of above match → Classify as `minor_text` (default)

3. **Store Classification**:
   - Store classified change type in `document_diffs.change_type` field
   - Use classification for prioritization (urgent changes get 2-day SLA vs 7-day default)

## 5.4 Rule Parsing Pipeline

### AI-Assisted Extraction

**Prompt Template**:
```
You are an immigration rule extraction system. Extract structured eligibility 
requirements from the following UK immigration rule text.

Rules:
1. Only extract explicitly stated requirements
2. Do not infer or assume
3. Output JSON with this structure:
{
  "visa_code": "SKILLED_WORKER",
  "requirements": [
    {
      "requirement_code": "MIN_SALARY",
      "description": "Minimum salary threshold",
      "condition_expression": {"">="": [{"var": "salary"}, 38700]},
      "source_excerpt": "Applicants must earn at least £38,700 per year"
    }
  ]
}

Text to extract from:
{extracted_text}
```

**Output Processing**:
1. Parse LLM JSON response
2. Validate JSON Logic expressions
3. Store in `parsed_rules` with:
   - `status = 'pending'`
   - `confidence_score` from LLM (if provided) or compute based on extraction quality
4. Create `rule_validation_tasks`

### Confidence Scoring

**Step-by-Step Implementation**:

1. **Initialize Base Score**:
   - Start with base confidence score of 0.5 (50%)

2. **Validate Numeric Values**:
   - Extract numeric values from source text (e.g., salary thresholds, fees)
   - Check if extracted logic contains matching numeric values
   - If match found → Add 0.2 to confidence score

3. **Validate Requirement Codes**:
   - Check if extracted requirement codes match standard codes (MIN_SALARY, SPONSOR_LICENSE, etc.)
   - If standard code found → Add 0.2 to confidence score

4. **Validate JSON Logic Expression**:
   - Check if `condition_expression` is valid JSON Logic syntax
   - If valid → Add 0.1 to confidence score

5. **Final Score**:
   - Cap maximum score at 1.0 (100%)
   - Store confidence score in `parsed_rules.confidence_score` field
   - Use score to determine if auto-approval is safe (typically >0.95) or requires human review

## 5.5 Human Validation Workflow

### Validation Task Assignment

1. **Auto-Assignment**:
   - Round-robin among active reviewers
   - Or workload-based (least busy reviewer)
   - Or expertise-based (reviewer specializes in visa type)

2. **Notification**:
   - Email to assigned reviewer
   - In-app notification
   - Slack/Teams integration (optional)

3. **Reviewer Interface** (Admin Console):
   - Side-by-side comparison: Original text vs Extracted logic
   - Diff view showing what changed
   - Edit capability for `condition_expression`
   - Approve/Reject/Request Changes buttons

4. **Approval Flow**:
   - Reviewer approves → Status = `approved`
   - Publisher service promotes to production
   - Previous rule version closed (`effective_to` set)

5. **Rejection Flow**:
   - Reviewer rejects → Status = `rejected`
   - `parsed_rules` marked as rejected
   - Admin can investigate and re-parse

### SLA Handling

- **Default SLA**: 7 days for validation
- **Urgent Changes**: Fee changes, threshold changes → 2 days SLA
- **Escalation**: If SLA exceeded → Notify senior reviewer
- **Auto-Approve** (optional): If confidence > 0.95 and no conflicts → Auto-approve with admin notification

## 5.6 Publishing Rules

### Promotion Process

**Step-by-Step Implementation**:

1. **Load Approved Rule**:
   - Retrieve `parsed_rule` by ID from `parsed_rules` table
   - Verify status is `approved`
   - Load associated `visa_type` using `visa_code`

2. **Create New Rule Version**:
   - Insert new row into `visa_rule_versions` table
   - Set `visa_type_id` from parsed rule
   - Set `effective_from` to detected effective date (or current date if not specified)
   - Link to `source_document_version_id` from parsed rule

3. **Create Requirements**:
   - For each requirement in parsed rule's extracted requirements:
     - Insert row into `visa_requirements` table
     - Set `rule_version_id` to newly created rule version
     - Store `requirement_code`, `description`, and `condition_expression` (JSON Logic)

4. **Close Previous Version**:
   - Query for active rule version for same visa type
   - If previous version exists:
     - Update `effective_to` to one day before new version's `effective_from`
     - This ensures no gap and no overlap in effective dates

5. **Update pgvector**:
   - Re-chunk new document version
   - Generate embeddings for new chunks
   - Store in pgvector (PostgreSQL) with metadata (document_version_id, source_url, effective_date, visa_code)
   - Mark old chunks as deprecated (don't delete, preserve for citations)

6. **Notify Users (Optional)**:
   - Send notification to users with active cases for affected visa type
   - Message: "Rules updated for [Visa Type] visa - you may want to re-check your eligibility"

## 5.7 pgvector Sync

### Chunking Strategy

1. **Document Chunking**:
   - Split by sections/paragraphs
   - Target chunk size: 500-1000 tokens
   - Overlap: 100 tokens between chunks

2. **Metadata**:
   - `document_version_id`: Link back to source
   - `source_url`: Original URL
   - `effective_date`: Rule effective date
   - `visa_code`: Associated visa type
   - `page_number`: For PDFs

3. **Embedding**:
   - Model: `text-embedding-ada-002` (OpenAI) or similar
   - Store in pgvector (PostgreSQL) with metadata

4. **Update Process**:
   - On rule publication → Re-chunk new document version
   - Embed and store in pgvector (PostgreSQL)
   - Mark old chunks as `deprecated` (don't delete, for citations)

## 5.8 Failure Handling

### Scraper Failures

- **Network Errors**: Retry with exponential backoff (max 3 attempts)
- **HTTP 404**: Source removed → Mark `data_sources.is_active = false`, alert admin
- **HTTP 403**: Blocked → Alert admin, may need to adjust user-agent or rate limits
- **Timeout**: Increase timeout, retry
- **Malformed Content**: Log error, skip this fetch, alert admin

### Parser Failures

- **LLM Timeout**: Retry with shorter context
- **Invalid JSON**: Log error, create validation task with raw extraction
- **Low Confidence**: Auto-flag for human review

### Publisher Failures

- **DB Transaction Failures**: Rollback, retry
- **pgvector Failures**: Queue for retry, don't block rule publication
- **Conflicting Rules**: Detect overlaps → Escalate to admin, don't auto-publish

## 5.9 Monitoring & Alerts

### Metrics to Track

- Fetch success rate per source
- Change detection frequency
- Parsing confidence distribution
- Validation task completion time
- Rule publication latency

### Alerts

- Source fetch failure (3 consecutive failures)
- High change frequency (potential source instability)
- Low parsing confidence (<0.6 average)
- Validation SLA breaches
- Rule conflicts detected

---

# Section 6: AI Reasoning & Rule Engine Flow

## 6.1 Hybrid Architecture Overview

The system combines **deterministic rule evaluation** (for hard requirements like salary thresholds) 
with **AI reasoning** (for nuanced interpretation and explanation). This hybrid approach reduces hallucinations 
and legal risk.

### Decision Flow

```
Case Facts
    ↓
┌─────────────────────────────────────┐
│   DETERMINISTIC RULE ENGINE         │
│   - Evaluate JSON Logic expressions │
│   - Check hard requirements         │
│   - Compute pass/fail per rule     │
└──────────────┬──────────────────────┘
               ↓
        Rule Results (pass/fail/missing)
               ↓
┌─────────────────────────────────────┐
│   AI REASONING SERVICE (RAG)        │
│   - Retrieve relevant rule context  │
│   - Generate nuanced explanation    │
│   - Extract citations               │
│   - Compute confidence score         │
└──────────────┬──────────────────────┘
               ↓
        Combined Outcome
    (likely/possible/unlikely)
```

## 6.2 Rule Engine Evaluation

### Step 1: Load Case Facts

**Step-by-Step Implementation**:

1. **Query Case Facts**:
   - Query `case_facts` table filtering by `case_id`
   - Order results by `created_at DESC` (most recent first)
   - Select `fact_key` and `fact_value` columns

2. **Convert to Dictionary**:
   - Parse JSONB `fact_value` fields into native data types
   - Build flat dictionary mapping `fact_key` → `fact_value`
   - Handle duplicates: If same `fact_key` appears multiple times, use the most recent (first in DESC order)

3. **Return Fact Dictionary**:
   - Return dictionary ready for rule evaluation
   - Example: `{"age": 29, "salary": 42000, "nationality": "NG", "has_sponsor": true}`

### Step 2: Load Active Rule Version

**Step-by-Step Implementation**:

1. **Determine Evaluation Date**:
   - Use provided `evaluation_date` if given
   - Otherwise use current date (today)

2. **Query Active Rule Version**:
   - Query `visa_rule_versions` table filtering by:
     - `visa_type_id` matches
     - `effective_from <= evaluation_date`
     - `effective_to IS NULL OR effective_to >= evaluation_date`
   - Order by `effective_from DESC` to get most recent version first
   - Limit to 1 result

3. **Handle Edge Cases**:
   - If no active version found → Return error (rule version missing)
   - If multiple versions match (shouldn't happen with proper versioning) → Use most recent

4. **Return Rule Version**:
   - Return rule version object with all fields needed for evaluation

### Step 3: Evaluate Requirements

**Step-by-Step Implementation**:

1. **Load Requirements**:
   - Query `visa_requirements` table for the rule version
   - Get all requirements with their `condition_expression` (JSON Logic)

2. **For Each Requirement**:
   a. **Parse JSON Logic Expression**:
      - Load `condition_expression` from requirement
      - Validate it's valid JSON Logic syntax
   
   b. **Evaluate Against Facts**:
      - Use JSON Logic evaluator library
      - Pass case facts as variables
      - Execute expression to get boolean result
   
   c. **Detect Missing Variables**:
      - Extract all variable names referenced in expression (e.g., "salary", "age")
      - Check which variables are missing from case facts
      - Return list of missing variable names
   
   d. **Handle Errors**:
      - If KeyError (missing variable) → Mark as failed, return missing variable name
      - If invalid expression → Mark as failed, return error message
      - If evaluation succeeds → Return pass/fail result

3. **Return Evaluation Result**:
   - For each requirement, return object containing:
     - `requirement_id`: ID of requirement
     - `requirement_code`: Code (e.g., "MIN_SALARY")
     - `passed`: Boolean result
     - `missing_facts`: List of missing variable names (if any)
     - `evaluation_details`: Full expression, facts used, result

### Step 4: Aggregate Results

**Step-by-Step Implementation**:

1. **Count Results**:
   - Count total number of requirements evaluated
   - Count how many passed (result = true)
   - Count how many failed (result = false)
   - Count how many have missing facts

2. **Compute Confidence Score**:
   - If total = 0 → Confidence = 0.0
   - Otherwise → Confidence = (passed requirements) / (total requirements)
   - Round to 2 decimal places

3. **Map to Outcome**:
   - If confidence >= 0.8 AND no missing facts → Outcome = "likely"
   - If confidence >= 0.5 → Outcome = "possible"
   - Otherwise → Outcome = "unlikely"

4. **Build Result Object**:
   - Return object containing:
     - `outcome`: "likely", "possible", or "unlikely"
     - `confidence`: Numeric score (0.0 to 1.0)
     - `requirements_passed`: Count of passed requirements
     - `requirements_total`: Total count
     - `requirements_failed`: Count of failed requirements
     - `missing_requirements`: List of requirements with missing facts

## 6.3 AI Reasoning Service (RAG)

### Step 1: Retrieve Relevant Context

**Step-by-Step Implementation**:

1. **Construct Query String**:
   - Build natural language query from case facts
   - Include: visa type name, applicant nationality, salary, sponsor status
   - Example: "Eligibility requirements for Skilled Worker visa. Applicant nationality: NG. Salary: 42000. 
   - Has sponsor: true."

2. **Query pgvector**:
   - Use pgvector query API with:
     - Query text (from step 1)
     - `top_k`: Retrieve top 5-10 most relevant chunks
     - Filters:
       - `visa_code`: Match visa type code
       - `effective_date`: Only chunks with effective date <= rule version effective date
     - `include_metadata`: True (to get source URLs, document version IDs)

3. **Extract Chunks and Metadata**:
   - For each retrieved result:
     - Extract chunk text
     - Extract metadata: `source_url`, `document_version_id`, `page_number` (if PDF)
     - Extract relevance score
     - Create excerpt (first 200 characters of text)

4. **Return Context Chunks**:
   - Return array of context objects, each containing:
     - `text`: Full chunk text
     - `source_url`: Original source URL
     - `document_version_id`: Link to document version
     - `excerpt`: Short preview
     - `score`: Relevance score

### Step 2: Construct AI Prompt

**Step-by-Step Implementation**:

1. **Build Prompt Structure**:
   - Start with system role: "You are an immigration eligibility assessment system. 
   - Your role is to provide decision support and information interpretation—NOT legal advice."

2. **Include Case Facts**:
   - Format case facts as JSON with indentation
   - Include all facts: age, nationality, salary, sponsor status, etc.

3. **Include Rule Evaluation Results**:
   - Format rule evaluation results showing which requirements passed/failed
   - Include requirement codes and descriptions

4. **Include Relevant Immigration Rules**:
   - Format retrieved context chunks
   - Show source URLs and excerpts
   - This is the RAG context that grounds the AI response

5. **Define Task**:
   - List what AI should do:
     - Review case facts against rules
     - Provide nuanced assessment
     - Generate confidence score
     - Identify missing documents/information
     - Provide source citations

6. **Specify Output Format**:
   - Define JSON structure with required fields:
     - `outcome`: "likely", "possible", or "unlikely"
     - `confidence`: 0.0-1.0 numeric score
     - `reasoning_summary`: Brief explanation
     - `detailed_reasoning`: Full explanation
     - `missing_documents`: Array of document type codes
     - `missing_information`: Array of missing fact keys
     - `citations`: Array of citation objects (source_url, excerpt, document_version_id)
     - `risk_flags`: Array of risk indicators
     - `recommendations`: Array of actionable recommendations

7. **Add Important Constraints**:
   - Only cite sources from provided context
   - Don't make claims without citations
   - Set confidence < 0.7 if uncertain (triggers human review)
   - Do not provide legal advice

8. **Return Complete Prompt**:
   - Return formatted prompt string ready for LLM

### Step 3: Call LLM

**Step-by-Step Implementation**:

1. **Prepare LLM Request**:
   - Use LLM API (OpenAI, Anthropic, etc.)
   - Set model (e.g., "gpt-4" or "claude-3")
   - Configure messages:
     - System message: "You are an immigration eligibility assessment system."
     - User message: The constructed prompt from Step 2
   - Set parameters:
     - `temperature`: 0.1 (low for consistency)
     - `max_tokens`: 2000 (limit response length)

2. **Make API Call**:
   - Send request to LLM API
   - Handle timeout (set reasonable timeout, e.g., 30 seconds)
   - Handle rate limiting (retry with exponential backoff if rate limited)

3. **Parse Response**:
   - Extract content from LLM response
   - Try to parse as JSON
   - If JSON parsing fails:
     - Attempt to extract JSON from text (may be wrapped in markdown code blocks)
     - If still fails → Log error, return failure status

4. **Validate Response Structure**:
   - Check that response contains required fields
   - Validate confidence score is between 0.0 and 1.0
   - Validate outcome is one of: "likely", "possible", "unlikely"

5. **Return Result**:
   - If successful:
     - Return object with:
       - `success`: true
       - `reasoning`: Parsed JSON response
       - `model`: Model name used
       - `tokens_used`: Token count (for cost tracking)
   - If failed:
     - Return object with:
       - `success`: false
       - `error`: Error message

### Step 4: Store Reasoning & Citations

**Step-by-Step Implementation**:

1. **Store Reasoning Log**:
   - Insert row into `ai_reasoning_logs` table:
     - `case_id`: Link to case
     - `prompt`: Full prompt sent to LLM (for auditability)
     - `response`: Full JSON response from LLM (stored as JSONB)
     - `model_name`: Model used (e.g., "gpt-4")
     - `created_at`: Timestamp
   - Get generated `id` from insert

2. **Store Citations**:
   - For each citation in reasoning output:
     - Insert row into `ai_citations` table:
       - `reasoning_log_id`: Link to reasoning log
       - `document_version_id`: Link to source document version
       - `excerpt`: Relevant text excerpt from source
     - This creates traceability chain: AI output → Citation → Document Version → Source URL

3. **Return Reasoning Log ID**:
   - Return the `id` of created reasoning log
   - This ID links eligibility results to AI reasoning

## 6.4 Combined Outcome Computation

**Step-by-Step Implementation**:

1. **Load Prerequisites**:
   - Load case facts for the case (using Step 1 from Rule Engine)
   - Load active rule version for visa type (using Step 2 from Rule Engine)
   - Load visa type details (name, code, etc.)
   - Load all requirements for the rule version

2. **Run Rule Engine Evaluation**:
   - Evaluate each requirement against case facts (using Step 3 from Rule Engine)
   - Aggregate results to get rule outcome (using Step 4 from Rule Engine)
   - This gives deterministic pass/fail result

3. **Run AI Reasoning (RAG)**:
   - Retrieve relevant context from pgvector (using Step 1 from AI Reasoning)
   - Construct AI prompt (using Step 2 from AI Reasoning)
   - Call LLM (using Step 3 from AI Reasoning)
   - Store reasoning and citations (using Step 4 from AI Reasoning)

4. **Handle AI Service Failure**:
   - If AI call fails (service unavailable, timeout, etc.):
     - Use rule engine outcome as final outcome
     - Set `ai_reasoning_available = false`
     - Add warning: "AI reasoning unavailable, using rule engine only"
     - Proceed with rule engine outcome only

5. **Combine Outcomes (If AI Succeeded)**:
   - **Check for Conflicts**:
     - If rule outcome = "unlikely" AND AI outcome = "likely":
       - This is a conflict (rule says no, AI says yes)
       - Set final outcome = "possible" (conservative)
       - Set confidence = minimum of rule confidence and AI confidence
       - Set `requires_human_review = true`
       - Set `conflict_reason = "Rule engine and AI reasoning conflict"`
   
   - **If No Conflict**:
     - Use AI outcome as final (AI provides nuance and explanation)
     - Use AI confidence score
     - Include AI reasoning summary, citations, missing documents, risk flags
     - Link to reasoning log ID

6. **Store Eligibility Result**:
   - Insert row into `eligibility_results` table:
     - `case_id`: Link to case
     - `visa_type_id`: Visa type evaluated
     - `rule_version_id`: Rule version used (for traceability)
     - `outcome`: Final outcome ("likely", "possible", "unlikely")
     - `confidence`: Final confidence score
     - `created_at`: Timestamp
   - Get generated `id` from insert

7. **Check for Human Review**:
   - If final confidence < 0.6 OR `requires_human_review = true`:
     - Create review task (see Section 7.1)
     - Set reason: "low_confidence_or_conflict"
     - Assign to available reviewer

8. **Return Final Outcome**:
   - Return complete outcome object with:
     - Outcome, confidence, reasoning, citations, missing documents, risk flags
     - Flags indicating if human review is required

## 6.5 Low-Confidence Escalation

### Automatic Escalation Triggers

1. **Confidence < 0.6**: AI uncertain
2. **Rule-AI Conflict**: Deterministic rules conflict with AI reasoning
3. **Missing Critical Facts**: Required facts not provided
4. **Edge Case Detected**: Borderline salary, unusual circumstances
5. **Citation Issues**: AI cannot find relevant sources

### Escalation Flow

**Step-by-Step Implementation**:

1. **Create Review Record**:
   - Insert row into `reviews` table:
     - `case_id`: Link to case requiring review
     - `status`: Set to `'in_progress'` initially
     - `created_at`: Timestamp
   - Get generated `id` from insert

2. **Assign Reviewer**:
   - Query available reviewers (role = 'reviewer', is_active = true)
   - Apply assignment strategy (round-robin or workload-based - see Section 7.2)
   - Update `reviews.reviewer_id` with assigned reviewer ID
   - If no reviewers available → Leave unassigned, will be assigned later

3. **Notify Reviewer**:
   - Send notification to assigned reviewer:
     - Email notification
     - In-app notification
     - Include: case ID, reason for review, urgency level
   - If no reviewer assigned → Notify admin to assign manually

4. **Update Case Status**:
   - Update `cases.status` to `'awaiting_review'`
   - This prevents further automated processing until review complete

5. **Log Audit Event**:
   - Create audit log entry:
     - `action`: "review.created"
     - `entity_type`: "case"
     - `entity_id`: case_id
     - `metadata`: Include reason for review

## 6.6 Handling Edge Cases

### Partial or Missing User Data

- **Missing Facts**: Rule engine returns `missing_facts` list, AI reasoning notes gaps
- **Partial Submissions**: System allows incremental fact submission, re-evaluates on update
- **Invalid Fact Values**: Validation at API level, rejected before evaluation

### AI Uncertainty or Low-Confidence Outcomes

- **Low Confidence (<0.6)**: Auto-escalate to human, show warning to user
- **Conflicting Sources**: AI flags conflict, human review required
- **No Relevant Context**: AI notes "insufficient source material", human review

### Changes in Government Rules

- **Rule Versioning**: System uses `effective_from` date to select correct rule version
- **Multiple Versions**: If case spans rule change, evaluate against both versions, show comparison
- **Rule Conflicts**: Detected during ingestion, human validation required before publishing

### System Downtime / Service Unavailability

- **AI Service Down**: Fallback to rule engine only, confidence reduced, user notified
- **pgvector Down**: Use rule engine + cached citations, degrade gracefully
- **Database Down**: Return 503, retry with exponential backoff

---

# Section 7: Human-in-Loop Validation Flow

## 7.1 Review Workflow Overview

Human reviewers serve as the **authority layer** over AI decisions, ensuring regulatory compliance and handling
edge cases.

### Review Triggers

1. **Automatic Escalation**:
   - AI confidence < 0.6
   - Rule-AI conflict detected
   - Missing critical documents
   - Edge case flags

2. **User Request**:
   - User clicks "Request Review"
   - User provides note/question

3. **Admin Assignment**:
   - Admin manually assigns case for review
   - Quality assurance sampling

## 7.2 Reviewer Assignment

### Assignment Strategies

**Round-Robin Assignment**:

**Step-by-Step Implementation**:

1. **Query Available Reviewers**:
   - Query `users` table filtering by:
     - `role = 'reviewer'`
     - `is_active = true`
   - Order by `last_assigned_at NULLS FIRST` (reviewers never assigned come first, then by last assignment time)

2. **Select Reviewer**:
   - Take first reviewer from ordered list
   - If no reviewers found → Return null (no assignment possible)

3. **Update Last Assigned Time**:
   - Update `users.last_assigned_at` to current timestamp
   - This tracks assignment order for next round-robin cycle

4. **Return Reviewer ID**:
   - Return selected reviewer's ID

**Workload-Based Assignment**:

**Step-by-Step Implementation**:

1. **Query Reviewers with Workload Count**:
   - Query `users` table joined with `reviews` table:
     - Left join on `reviews.reviewer_id = users.id AND reviews.status = 'in_progress'`
     - Filter: `users.role = 'reviewer' AND users.is_active = true`
     - Group by `users.id`
     - Count active reviews per reviewer
     - Order by active review count ASC (least busy first)
     - Limit to 1 result

2. **Select Reviewer**:
   - Take reviewer with lowest active review count
   - If multiple reviewers tied → Use round-robin as tiebreaker
   - If no reviewers found → Return null

3. **Return Reviewer ID**:
   - Return selected reviewer's ID

**Expertise-Based** (Future):
- Match reviewer expertise (visa type, jurisdiction) to case

## 7.3 Reviewer Console Interface

### Review Dashboard

**GET /api/v1/reviewer/dashboard**

Shows:
- Assigned reviews (status: `in_progress`, `pending`)
- SLA deadlines
- Case summaries with risk flags
- Quick actions: Start Review, Complete Review, Request More Info

### Review Detail View

**GET /api/v1/reviews/{review_id}**

Shows:
- Case facts
- AI eligibility results with full reasoning
- Rule evaluation details
- Uploaded documents
- User notes/questions
- Previous review history (if any)

### Reviewer Actions

1. **Approve AI Decision**:
   - Reviewer agrees with AI → Mark review complete
   - No override needed

2. **Override Decision**:
   - Reviewer disagrees → Create `decision_overrides` entry
   - Provide reasoning
   - Original AI result preserved

3. **Request More Information**:
   - Reviewer needs additional facts/documents
   - Create note → Notify user → Case status = `awaiting_user_input`

4. **Escalate to Senior Reviewer**:
   - Complex case → Reassign to senior reviewer
   - Add escalation note

## 7.4 Override Process

### Creating Overrides

**Step-by-Step Implementation**:

1. **Validate Input**:
   - Verify reviewer has permission to create override
   - Verify review is assigned to this reviewer (or reviewer is admin)
   - Validate `overridden_outcome` is one of: "likely", "possible", "unlikely"
   - Verify `original_result_id` exists and belongs to the case

2. **Store Override**:
   - Insert row into `decision_overrides` table:
     - `case_id`: Link to case
     - `original_result_id`: Link to eligibility result being overridden
     - `overridden_outcome`: New outcome from reviewer
     - `reason`: Explanation for override
     - `reviewer_id`: ID of reviewer creating override
     - `created_at`: Timestamp
   - Get generated `id` from insert

3. **Add Review Note**:
   - Insert row into `review_notes` table:
     - `review_id`: Link to review
     - `note`: Text describing override (e.g., "Override created: [reason]")
     - `created_at`: Timestamp
   - This provides context for why override was created

4. **Update Review Status**:
   - Update `reviews` table:
     - Set `status = 'completed'`
     - Set `completed_at` to current timestamp
   - This marks review as finished

5. **Update Case Status**:
   - Update `cases` table:
     - Set `status = 'reviewed'`
   - This indicates case has been reviewed by human

6. **Log Audit Event**:
   - Create entry in `audit_logs` table:
     - `actor_id`: Reviewer ID
     - `action`: "decision_override"
     - `entity_type`: "eligibility_result"
     - `entity_id`: Original result ID
     - `metadata`: JSONB containing override ID and reason
     - `timestamp`: Current timestamp
   - This creates immutable audit trail

7. **Return Override ID**:
   - Return the `id` of created override
   - This can be used to link override to other records

### Override Precedence

**Step-by-Step Implementation**:

1. **Display Logic for Eligibility Results**:
   - When retrieving eligibility results for display, always check for decision overrides first
   - Query pattern: Join `eligibility_results` with `decision_overrides` on `original_result_id`
   - Use COALESCE to return override outcome if exists, otherwise return AI outcome
   - Always show both AI outcome and human outcome (if override exists) for transparency

2. **Override Resolution**:
   - If multiple overrides exist for same result, use the most recent one (by `created_at`)
   - Preserve full history: Show all overrides in audit trail
   - When displaying to user, clearly indicate if result was overridden by human reviewer

3. **Multi-Reviewer Conflicts**:
   - If two reviewers create conflicting overrides, latest override wins
   - Log conflict in audit trail
   - Notify senior reviewer for resolution if conflicts detected

4. **SLA Handling**:
   - Track review creation time vs completion time
   - Alert if review exceeds SLA (default: 7 days, urgent: 2 days)
   - Auto-escalate to senior reviewer if SLA breached

---

# Section 8: Document Upload & Checking

## 8.1 Document Upload Workflow

### Step-by-Step Implementation

1. **File Upload Endpoint**:
   - Accept multipart/form-data requests
   - Validate file size (max 10MB per file)
   - Validate file type (PDF, JPG, PNG only)
   - Generate unique file identifier (UUID)
   - Store file in encrypted S3 bucket with path: `cases/{case_id}/{document_id}.{ext}`

2. **File Storage**:
   - Upload to S3 with server-side encryption (SSE-S3 or SSE-KMS)
   - Store metadata in `case_documents` table:
     - `case_id`, `document_type_id` (nullable initially), `file_path`, `uploaded_at`
   - Set initial status as `uploaded`

3. **Asynchronous Processing**:
   - Queue document for processing (use job queue: Celery, Bull, etc.)
   - Process in background: OCR → Classification → Validation

## 8.2 OCR Processing

### Step-by-Step Implementation

1. **OCR Extraction**:
   - Use OCR service (Tesseract, AWS Textract, Google Vision API)
   - Extract text from document
   - Store extracted text in `case_documents.ocr_text` field
   - Handle multiple languages if needed

2. **OCR Quality Check**:
   - Validate OCR success (text length > 0)
   - Check for common OCR errors (character recognition confidence)
   - Create `document_checks` entry:
     - `check_type = 'ocr'`
     - `result = 'pass'` if successful, `'fail'` if failed
     - Store error details if failed

3. **Edge Cases**:
   - If OCR fails: Mark check as failed, allow user to retry upload
   - If low confidence: Mark as warning, flag for human review
   - If document is image-only (no text): Mark OCR as N/A, proceed with classification

## 8.3 Document Classification ✅ **FULLY IMPLEMENTED**

### Step-by-Step Implementation

1. **AI Classification** ✅:
   - ✅ Use LLM to classify document type (`DocumentClassificationService`)
   - ✅ Input: OCR text + file metadata (filename, size)
   - ✅ Output: Predicted `document_type_id` with confidence score
   - ✅ Comprehensive prompts in `helpers/prompts.py` (`build_document_classification_prompt`)
   - ✅ LLM calls use `external_services` pattern via `helpers/llm_helper.py`
   - ✅ Production-ready: retry logic, rate limiting, circuit breaker, error handling

2. **Classification Logic** ✅:
   - ✅ Match against known document types (passport, bank_statement, certificate_of_sponsorship, etc.)
   - ✅ If confidence < 0.7: Flag for human review
   - ✅ Update `case_documents.document_type_id` if confidence >= 0.7
   - ✅ Create `document_checks` entry:
     - `check_type = 'classification'`
     - `result = 'pass'` if confident, `'warning'` if low confidence

3. **Manual Override** ✅:
   - ✅ Allow user to manually select document type if classification uncertain
   - ✅ Allow reviewer to correct classification

4. **Prompt Architecture** ✅:
   - ✅ All prompts centralized in `helpers/prompts.py`
   - ✅ System messages in helpers (`get_classification_system_message`)
   - ✅ Comprehensive guidelines and document type descriptions
   - ✅ Document type indicators and classification rules

## 8.4 Document Validation

### Step-by-Step Implementation

1. **Requirement Matching** ✅ **FULLY IMPLEMENTED**:
   - ✅ `DocumentRequirementMatchingService` - Matches documents against visa document requirements
   - ✅ Loads `visa_document_requirements` for case's visa type and rule version
   - ✅ Checks if uploaded document matches required document type
   - ✅ Evaluates conditional logic against case facts using RuleEngineService
   - ✅ Creates `document_checks` entry with `check_type='requirement_match'`
   - ✅ Returns result: 'passed' if matches, 'failed' if doesn't match, 'warning' if conditional logic not satisfied
   - ✅ Integrated into document processing workflow (Step 5)
   - ✅ Comprehensive error handling and logging

2. **Content Validation** ✅ **FULLY IMPLEMENTED**:
   - ✅ `DocumentContentValidationService` - Validates document content against case facts using LLM
   - ✅ Comprehensive validation prompts in `helpers/prompts.py` (`build_content_validation_prompt`)
   - ✅ Document-type specific validation guidance (passport, visa, bank_statement, etc.)
   - ✅ Field-by-field matching instructions (names, dates, numbers, nationality)
   - ✅ Validates names, dates, numbers, nationality against case facts
   - ✅ Returns validation status (passed/failed/warning/pending) with detailed results
   - ✅ Creates `DocumentCheck` with `check_type='content_validation'`
   - ✅ Stores validation results in `CaseDocument.content_validation_status` and `content_validation_details`
   - ✅ Integrated into document processing workflow (Step 4)
   - ✅ LLM calls use `external_services` pattern via `helpers/llm_helper.py`
   - ✅ Admin endpoints support filtering by content validation status
   - ✅ Check document expiry dates - ✅ **FULLY IMPLEMENTED** (see Section 8.7.1)
   - ⚠️ Verify signatures if applicable - Planned

3. **Document Status Calculation**:
   - Aggregate all check results
   - Status = `verified` if all checks pass
   - Status = `rejected` if any critical check fails
   - Status = `warning` if non-critical checks fail

## 8.5 Document Checklist Generation

### Step-by-Step Implementation

1. **Load Requirements**:
   - Query `visa_document_requirements` for active rule version
   - Filter by `mandatory = true` for required documents
   - Include conditional requirements based on case facts (e.g., dependants require additional docs)

2. **Match Against Uploads**:
   - For each required document type:

## 8.6 Admin API Endpoints

### Step-by-Step Implementation

1. **Case Document Management**:
   - ✅ Admin endpoints implemented: `GET /api/v1/document-handling/admin/case-documents/`
   - ✅ Filter by: case_id, document_type_id, status, has_ocr_text, min_confidence, mime_type, date range
   - ✅ Admin detail endpoint: `GET /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Update endpoint: `PUT /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Bulk operations endpoint: `POST /api/v1/document-handling/admin/case-documents/bulk-operation/`
   - ✅ Bulk operations: delete, update_status, reprocess_ocr, reprocess_classification, reprocess_validation, reprocess_full

2. **Document Check Management**:
   - ✅ Admin endpoints implemented: `GET /api/v1/document-handling/admin/document-checks/`
   - ✅ Filter by: case_document_id, check_type, result, performed_by, date range
   - ✅ Admin detail endpoint: `GET /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Update endpoint: `PUT /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Bulk delete endpoint: `POST /api/v1/document-handling/admin/document-checks/bulk-operation/`

3. **Document Handling Analytics**:
   - ✅ Statistics endpoint: `GET /api/v1/document-handling/admin/statistics/`
   - ✅ Provides comprehensive statistics on:
     - Case documents: total, by status, OCR coverage, classification confidence, file sizes, recent activity, by document type
     - Document checks: total, by type, by result, failed/passed/warning/pending counts, recent activity
   - ✅ **Architecture**: Follows system architecture pattern (selectors, repositories, services, views)
   - ✅ **Documentation**: See `DOCUMENT_HANDLING_ADMIN_FUNCTIONALITY.md` for complete API documentation

## 8.7.1 Document Expiry Date Extraction

### Step-by-Step Implementation

1. **Expiry Date Extraction Service** ✅:
   - ✅ `DocumentExpiryExtractionService` - Uses LLM to extract expiry dates from OCR text
   - ✅ Comprehensive extraction prompts in `helpers/prompts.py` (`build_expiry_date_extraction_prompt`)
   - ✅ Document-type specific guidance (passport, visa, certificate, license)
   - ✅ Supports multiple document types (passport, visa, certificate, license)
   - ✅ Handles various date formats (DD/MM/YYYY, YYYY-MM-DD, ISO, written formats, etc.)
   - ✅ Key indicators search (Date of Expiry, Expires, Valid Until, etc.)
   - ✅ Confidence scoring guidelines and edge case handling
   - ✅ Returns expiry date, confidence score, and metadata
   - ✅ Stores expiry date in `CaseDocument.expiry_date` field
   - ✅ LLM calls use `external_services` pattern via `helpers/llm_helper.py`

2. **Expiry Date Validation**:
   - ✅ Helper methods: `is_expired()` - Check if expiry date has passed
   - ✅ Helper methods: `days_until_expiry()` - Calculate days until expiry
   - ✅ Integrated into document processing workflow (Step 3)

3. **Admin Support**:
   - ✅ Admin endpoints support filtering by `has_expiry_date`, `expiry_date_from`, `expiry_date_to`, `is_expired`
   - ✅ Admin serializers include `expiry_date`, `is_expired`, `days_until_expiry` fields
   - ✅ Statistics include expiry date metrics (with_expiry_date, expired, expiring_soon)

## 8.7.2 Content Validation Against Case Facts ✅ **FULLY IMPLEMENTED**

### Step-by-Step Implementation

1. **Content Validation Service** ✅:
   - ✅ `DocumentContentValidationService` - Validates document content against case facts using LLM
   - ✅ Comprehensive validation prompts in `helpers/prompts.py` (`build_content_validation_prompt`)
   - ✅ Document-type specific validation guidance (passport, visa, bank_statement, certificate_of_sponsorship)
   - ✅ Field-by-field matching instructions with confidence scoring
   - ✅ Compares document content (from OCR) with case facts
   - ✅ Validates: names, dates, numbers, nationality, identifiers
   - ✅ Returns validation status: passed, failed, warning, pending
   - ✅ Returns detailed results: matched_fields, mismatched_fields, missing_fields, confidence
   - ✅ LLM calls use `external_services` pattern via `helpers/llm_helper.py`

2. **Validation Integration** ✅:
   - ✅ Integrated into document processing workflow (Step 4)
   - ✅ Creates `DocumentCheck` with `check_type='content_validation'`
   - ✅ Stores validation results in `CaseDocument.content_validation_status` and `content_validation_details`
   - ✅ Updates document status based on validation results

3. **Admin Support** ✅:
   - ✅ Admin endpoints support filtering by `content_validation_status`
   - ✅ Admin serializers include `content_validation_status`, `content_validation_details`, `content_validation_summary` fields
   - ✅ Statistics include content validation metrics (by_status, passed, failed, warning)

## 8.8 Document Processing Job Tracking ✅ **FULLY INTEGRATED**

### Step-by-Step Implementation

1. **Processing Job Management** ✅:
   - ✅ Processing job model (`ProcessingJob`) tracks all document processing operations
   - ✅ **Integrated into document processing workflow**: `process_document_task` creates and updates `ProcessingJob` records
   - ✅ Celery task IDs are linked to processing jobs for tracking
   - ✅ Admin endpoints implemented: `GET /api/v1/document-processing/admin/processing-jobs/`
   - ✅ Filter by: case_document_id, status, processing_type, error_type, created_by_id, date range, priority, retry status
   - ✅ Admin detail endpoint: `GET /api/v1/document-processing/admin/processing-jobs/<id>/`
   - ✅ Update endpoint: `PUT /api/v1/document-processing/admin/processing-jobs/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-processing/admin/processing-jobs/<id>/`
   - ✅ Bulk operations endpoint: `POST /api/v1/document-processing/admin/processing-jobs/bulk-operation/`
   - ✅ Bulk operations: delete, cancel, retry, update_status, update_priority

2. **Processing History/Audit Logging** ✅:
   - ✅ Processing history model (`ProcessingHistory`) tracks all processing operations
   - ✅ **Integrated into document processing workflow**: All processing steps log to `ProcessingHistory`
   - ✅ History entries created for: OCR started/completed/failed, classification started/completed/failed, validation started/completed/failed, job started/completed/failed
   - ✅ Processing time tracking for each step
   - ✅ Error tracking with error types and messages
   - ✅ Admin endpoints implemented: `GET /api/v1/document-processing/admin/processing-history/`
   - ✅ Filter by: case_document_id, processing_job_id, action, status, error_type, user_id, date range
   - ✅ Admin detail endpoint: `GET /api/v1/document-processing/admin/processing-history/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-processing/admin/processing-history/<id>/`
   - ✅ Bulk delete endpoint: `POST /api/v1/document-processing/admin/processing-history/bulk-operation/`

3. **Document Processing Analytics** ✅:
   - ✅ Statistics endpoint: `GET /api/v1/document-processing/admin/statistics/`
   - ✅ Provides comprehensive statistics on:
     - Processing jobs: total, by status, by type, failed/completed/pending counts, average processing time, retry statistics, recent activity
     - Processing history: total, by action, by status, failed/successful/warning counts, average processing time, recent activity
   - ✅ **Architecture**: Follows system architecture pattern (selectors, repositories, services, views)
   - ✅ **Documentation**: See `DOCUMENT_PROCESSING_ADMIN_FUNCTIONALITY.md` for complete API documentation

## 8.9 LLM Integration & Prompt Architecture ✅ **FULLY IMPLEMENTED**

### Step-by-Step Implementation

1. **Prompt Centralization** ✅:
   - ✅ All LLM prompts centralized in `helpers/prompts.py`
   - ✅ Comprehensive prompts for all document processing operations:
     - ✅ Document classification (`build_document_classification_prompt`)
     - ✅ Expiry date extraction (`build_expiry_date_extraction_prompt`)
     - ✅ Content validation (`build_content_validation_prompt`)
   - ✅ System messages for each operation in helpers
   - ✅ Document-type specific guidance and instructions
   - ✅ Detailed instructions, edge case handling, and confidence scoring guidelines

2. **LLM Helper Architecture** ✅:
   - ✅ `helpers/llm_helper.py` provides centralized LLM call interface
   - ✅ Uses `external_services` pattern via `data_ingestion.helpers.llm_client`
   - ✅ Production-ready features:
     - ✅ Retry logic with exponential backoff
     - ✅ Rate limiting and circuit breaker
     - ✅ Timeout handling
     - ✅ Error classification (LLMRateLimitError, LLMTimeoutError, etc.)
     - ✅ Usage tracking and processing time metrics
   - ✅ JSON response parsing with markdown code block handling (`parse_llm_json_response`)

3. **Service Integration** ✅:
   - ✅ All services use `call_llm_for_document_processing()` from helpers
   - ✅ No direct OpenAI client calls in services
   - ✅ Consistent error handling across all LLM operations
   - ✅ Proper logging and observability
   - ✅ Services updated:
     - ✅ `DocumentClassificationService` - Uses helpers for LLM calls
     - ✅ `DocumentExpiryExtractionService` - Uses helpers for LLM calls
     - ✅ `DocumentContentValidationService` - Uses helpers for LLM calls

4. **Benefits** ✅:
   - ✅ Centralized prompt management - easier to maintain and update
   - ✅ Consistent LLM calls - retry logic, rate limiting, error handling
   - ✅ Better error handling - custom exceptions for different error types
   - ✅ Improved observability - usage tracking, processing time metrics
   - ✅ Easier testing - helpers can be mocked independently
   - ✅ Production-ready - circuit breaker, retry logic, timeout handling

## 8.5 Document Checklist Generation

### Step-by-Step Implementation

1. **Load Requirements**:
   - Query `visa_document_requirements` for active rule version
   - Filter by `mandatory = true` for required documents
   - Include conditional requirements based on case facts (e.g., dependants require additional docs)

2. **Match Against Uploads**:
   - For each required document type:
     - Check if `case_documents` exists with matching `document_type_id`
     - Check if document status is `verified`
   - Mark as: `provided`, `missing`, or `incomplete`

3. **Completion Percentage**:
   - Calculate: (provided mandatory docs) / (total mandatory docs) * 100
   - Display progress to user

## 8.6 Handling Failed Checks

### Step-by-Step Implementation

1. **User Notification**:
   - When document check fails, notify user via email/in-app notification
   - Show specific failure reason (e.g., "OCR failed: Image quality too low")
   - Provide actionable guidance (e.g., "Please upload a clearer image")

2. **Resubmission Flow**:
   - Allow user to delete failed document
   - Allow user to upload replacement document
   - Re-run checks on new upload

3. **Human Review for Uncertain Cases**:
   - If classification confidence < 0.7: Flag for reviewer

## 8.7 Admin API Endpoints

### Step-by-Step Implementation

1. **Case Document Management**:
   - ✅ Admin endpoints implemented: `GET /api/v1/document-handling/admin/case-documents/`
   - ✅ Filter by: case_id, document_type_id, status, has_ocr_text, min_confidence, mime_type, date range
   - ✅ Admin detail endpoint: `GET /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Update endpoint: `PUT /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-handling/admin/case-documents/<id>/`
   - ✅ Bulk operations endpoint: `POST /api/v1/document-handling/admin/case-documents/bulk-operation/`
   - ✅ Bulk operations: delete, update_status, reprocess_ocr, reprocess_classification, reprocess_validation, reprocess_full

2. **Document Check Management**:
   - ✅ Admin endpoints implemented: `GET /api/v1/document-handling/admin/document-checks/`
   - ✅ Filter by: case_document_id, check_type, result, performed_by, date range
   - ✅ Admin detail endpoint: `GET /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Update endpoint: `PUT /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Delete endpoint: `DELETE /api/v1/document-handling/admin/document-checks/<id>/`
   - ✅ Bulk delete endpoint: `POST /api/v1/document-handling/admin/document-checks/bulk-operation/`

3. **Document Handling Analytics**:
   - ✅ Statistics endpoint: `GET /api/v1/document-handling/admin/statistics/`
   - ✅ Provides comprehensive statistics on:
     - Case documents: total, by status, OCR coverage, classification confidence, file sizes, recent activity, by document type
     - Document checks: total, by type, by result, failed/passed/warning/pending counts, recent activity
   - ✅ **Architecture**: Follows system architecture pattern (selectors, repositories, services, views)
   - ✅ **Documentation**: See `DOCUMENT_HANDLING_ADMIN_FUNCTIONALITY.md` for complete API documentation
   - Reviewer can manually classify and approve

---

# Section 9: Security, GDPR, and Compliance

## 9.1 Role-Based Access Control (RBAC)

### Step-by-Step Implementation

1. **User Roles**:
   - Define roles: `user` (applicant), `reviewer`, `admin`
   - Store role in `users.role` field
   - Validate role on every API request

2. **Permission Matrix**:
   - **User Role**:
     - Can create/read/update own cases only
     - Can upload documents to own cases
     - Cannot access other users' cases
     - Cannot access admin endpoints
   
   - **Reviewer Role**:
     - Can read assigned reviews
     - Can read cases assigned for review
     - Can create decision overrides
     - Can read own cases (as user)
     - Cannot access admin rule management
   
   - **Admin Role**:
     - Full access to all cases
     - Can manage rule validation tasks
     - Can manage data sources
     - Can view audit logs
     - Can manage users

3. **Implementation Steps**:
   - Create middleware/guard that checks JWT token
   - Extract user role from token
   - Validate role has permission for requested action
   - Return 403 Forbidden if insufficient permissions

## 9.2 Data Encryption

### Step-by-Step Implementation

1. **Encryption at Rest**:
   - Enable database encryption (PostgreSQL TDE or cloud provider encryption)
   - Encrypt S3 objects (SSE-S3 or SSE-KMS)
   - Encrypt sensitive fields in database (PII fields like email, phone) using application-level encryption

2. **Encryption in Transit**:
   - Enforce HTTPS/TLS 1.3 for all API endpoints
   - Use secure connections for database (SSL/TLS)
   - Use secure connections for S3 (HTTPS)

3. **Key Management**:
   - Use cloud KMS (AWS KMS, Azure Key Vault, GCP KMS) for encryption keys
   - Rotate keys periodically (annually or as per compliance requirements)
   - Never store keys in code or environment variables (use secrets manager)

## 9.3 GDPR Compliance

### Step-by-Step Implementation

1. **Data Minimization**:
   - Only collect necessary PII (name, email, nationality, DOB for eligibility)
   - Separate `user_profiles` from `users` table for easier deletion
   - Don't store unnecessary data (e.g., full address if not required)

2. **Right to Erasure (Article 17)**:
   - Implement deletion endpoint: `DELETE /api/v1/users/{user_id}/data`
   - Steps:
     a. Soft delete user account (`users.is_active = false`)
     b. Anonymize `user_profiles` (replace PII with anonymized values)
     c. Delete or anonymize `case_facts` (remove PII, keep anonymized facts for analytics)
     d. Delete `case_documents` from S3 and database
     e. Retain anonymized `audit_logs` (required for compliance, but remove PII)
     f. Retain `eligibility_results` but remove user_id linkage
   - Complete deletion within 30 days of request
   - Send confirmation email to user

3. **Right to Access (Article 15)**:
   - Implement export endpoint: `GET /api/v1/users/{user_id}/data-export`
   - Export all user data in machine-readable format (JSON)
   - Include: profile, cases, facts, documents metadata, eligibility results
   - Exclude: internal system data, other users' data

4. **Consent Management**:
   - Store consent in `user_profiles.consent_given` and `consent_timestamp`
   - Require explicit consent before processing personal data
   - Allow users to withdraw consent (triggers data minimization)

5. **Data Portability (Article 20)**:
   - Provide data export in structured format (JSON)
   - Allow user to download their data

## 9.4 Audit Logging

### Step-by-Step Implementation

1. **Log All Critical Actions**:
   - Create `audit_logs` entry for:
     - User registration/login
     - Case creation/update/deletion
     - Eligibility check execution
     - Document uploads
     - Decision overrides
     - Rule publishing
     - Admin actions (user management, rule management)

2. **Audit Log Structure**:
   - `actor_id`: Who performed the action
   - `action`: What action (e.g., "case.created", "decision.overridden")
   - `entity_type`: What entity (e.g., "case", "eligibility_result")
   - `entity_id`: Which specific entity
   - `metadata`: Additional context (JSONB)
   - `timestamp`: When action occurred

3. **Audit Log Retention**:
   - Retain logs for minimum 7 years (legal requirement)
   - Archive old logs (>1 year) to cold storage
   - Never delete audit logs (even for GDPR erasure, anonymize only)

4. **Audit Log Querying**:
   - Provide admin endpoint to query audit logs
   - Filter by: actor, action, entity, date range
   - Export audit logs for compliance audits

## 9.5 Handling Sensitive Documents

### Step-by-Step Implementation

1. **Document Encryption**:
   - Encrypt documents before storing in S3
   - Use client-side encryption for highly sensitive documents (optional)
   - Use server-side encryption (SSE-KMS) as minimum

2. **Access Control**:
   - Only case owner and assigned reviewers can access documents
   - Generate time-limited signed URLs for document downloads (expire in 1 hour)
   - Log all document access in audit logs

3. **Document Retention**:
   - Retain documents for case duration + 7 years (legal requirement)
   - Auto-archive documents after case completion
   - Delete documents on user erasure request (GDPR)

## 9.6 Logging and Alerting for Suspicious Activities

### Step-by-Step Implementation

1. **Suspicious Activity Detection**:
   - Monitor for:
     - Multiple failed login attempts (>5 in 10 minutes)
     - Unauthorized access attempts (403 errors)
     - Unusual API usage patterns (rate limit violations)
     - Bulk data export requests
     - Admin action outside business hours

2. **Alerting**:
   - Send alerts to security team via email/Slack
   - Log all suspicious activities in security audit log
   - Auto-block user account if suspicious activity detected

3. **Rate Limiting**:
   - Implement rate limits per user/IP
   - Limit: 100 requests per minute per user
   - Limit: 10 document uploads per hour per user
   - Return 429 Too Many Requests if exceeded

---

# Section 10: Step-by-Step Implementation Plan

## 10.1 Module List with Dependencies

### Core Modules (Build in Order)

1. **Database Module** (Foundation)
   - Dependencies: PostgreSQL 14+
   - Tasks: Create all tables, indexes, constraints
   - No dependencies on other modules

2. **Authentication Module**
   - Dependencies: Database Module
   - Tasks: JWT token generation/validation, password hashing, user registration/login

3. **Case Management Module**
   - Dependencies: Database Module, Authentication Module
   - Tasks: Case CRUD, fact collection, status management

4. **Rule Engine Module**
   - Dependencies: Database Module
   - Tasks: JSON Logic evaluator, requirement evaluation, outcome computation

5. **Document Service Module**
   - Dependencies: Database Module, Object Storage (S3), OCR Service
   - Tasks: File upload, OCR, classification, validation

6. **AI Reasoning Service Module**
   - Dependencies: Database Module, pgvector (PostgreSQL), LLM API
   - Tasks: RAG retrieval, prompt construction, LLM calls, citation extraction

7. **Ingestion Service (IRIMS)**
   - Dependencies: Database Module, Object Storage, LLM API
   - Tasks: Scraping, change detection, rule parsing, validation queue

8. **Review Service Module**
   - Dependencies: Database Module, Notification Service
   - Tasks: Review assignment, override management, reviewer console

9. **Admin Console Module**
   - Dependencies: All above modules
   - Tasks: Rule validation UI, data source management, audit log viewer

10. **Frontend Module**
    - Dependencies: All API modules
    - Tasks: User portal, reviewer console, admin dashboard

## 10.2 Recommended Tech Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: Django (Python) 
- **Database**: PostgreSQL 16+
- **Object Storage**: AWS S3
- **Job Queue**: Celery (Python) with Redis
- **Vector Storage**: pgvector (PostgreSQL extension) - recommended approach

### AI/ML
- **LLM API**: OpenAI GPT-4, Anthropic Claude, or self-hosted
- **Embeddings**: OpenAI text-embedding-ada-002 or similar
- **OCR**: Tesseract, AWS Textract, or Google Vision API

### Infrastructure
- **Hosting**: AWS
- **Containerization**: Docker + Kubernetes (or Docker Compose for MVP)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) or cloud logging

### Frontend
- **Framework**: React 18+ or Next.js
- **State Management**: Redux, Zustand, or Pinia
- **UI Library**: Material-UI, Ant Design, or Tailwind CSS

## 10.3 Development Order / Phased Approach

### Phase 1: MVP Foundation (Weeks 1-4)

**Week 1: Database & Infrastructure Setup**
1. Set up PostgreSQL database
2. Run all migration scripts to create tables
3. Set up S3 bucket for document storage
4. Set up basic CI/CD pipeline
5. Set up development environment (Docker Compose)

**Week 2: Authentication & Case Management**
1. Implement user registration/login (JWT)
2. Implement case creation API
3. Implement fact submission API
4. Implement case retrieval API
5. Write unit tests for core APIs

**Week 3: Rule Engine**
1. Implement JSON Logic evaluator
2. Implement requirement loading from database
3. Implement requirement evaluation against case facts
4. Implement outcome computation (likely/possible/unlikely)
5. Write unit tests with sample rules

**Week 4: Basic Eligibility Check**
1. Integrate rule engine with case service
2. Implement eligibility check endpoint
3. Store eligibility results in database
4. Return results to user
5. End-to-end test: Create case → Submit facts → Run eligibility check

### Phase 2: AI & Documents (Weeks 5-8)

**Week 5: Document Upload & OCR**
1. Implement file upload endpoint
2. Integrate OCR service
3. Store OCR text in database
4. Implement document classification (basic)
5. Test with sample documents

**Week 6: AI Reasoning Service**
1. Set up pgvector (PostgreSQL extension)
2. Implement document chunking and embedding
3. Implement RAG retrieval
4. Implement LLM prompt construction
5. Implement LLM call and response parsing
6. Store AI reasoning logs and citations

**Week 7: Hybrid Eligibility (Rule + AI)**
1. Integrate AI reasoning with rule engine
2. Implement combined outcome computation
3. Handle conflicts between rule engine and AI
4. Implement low-confidence escalation
5. End-to-end test: Full eligibility check with AI

**Week 8: Document Requirements & Checklist**
1. Implement document requirement loading
2. Implement document-checklist generation
3. Match uploaded documents against requirements
4. Calculate completion percentage
5. Display checklist to user

### Phase 3: Ingestion & Rules (Weeks 9-12)

**Week 9: Ingestion Service Foundation**
1. Set up scheduler (Airflow/Celery Beat)
2. Implement fetcher for HTML pages
3. Implement hash computation and change detection
4. Store source documents and versions
5. Test with sample gov.uk pages

**Week 10: Rule Parsing**
1. Implement diff engine
2. Implement AI-assisted rule extraction
3. Store parsed rules in staging area
4. Implement confidence scoring
5. Test rule extraction with sample documents

**Week 11: Human Validation Workflow**
1. Implement validation task creation
2. Implement reviewer assignment
3. Implement admin UI for rule validation
4. Implement approve/reject/edit flows
5. Test end-to-end: Change detected → Parsed → Validated → Published

**Week 12: Rule Publishing**
1. Implement rule promotion to production
2. Implement version closing (effective_to)
3. Implement pgvector sync on rule publish
4. Test rule updates flow end-to-end

### Phase 4: Human Review & Admin (Weeks 13-16)

**Week 13: Review Service**
1. Implement review creation (auto-escalation)
2. Implement reviewer assignment (round-robin/workload)
3. Implement review status management
4. Implement review notes

**Week 14: Decision Overrides**
1. Implement override creation
2. Implement override precedence logic
3. Update eligibility display to show overrides
4. Test override workflow

**Week 15: Reviewer Console**
1. Build reviewer dashboard UI
2. Build review detail view
3. Implement reviewer actions (approve, override, request info)
4. Test reviewer workflow end-to-end

**Week 16: Admin Console**
1. Build admin dashboard
2. Implement rule validation task management UI
3. Implement data source management UI
4. Implement audit log viewer
5. Test admin workflows

### Phase 5: Polish & Launch (Weeks 17-20)

**Week 17: Security & GDPR**
1. Implement RBAC enforcement
2. Implement data encryption
3. Implement GDPR endpoints (erasure, export)
4. Implement audit logging for all critical actions
5. Security audit and penetration testing

**Week 18: Error Handling & Edge Cases**
1. Implement comprehensive error handling
2. Handle all edge cases (missing data, service failures, conflicts)
3. Implement retry logic and fallbacks
4. Add monitoring and alerting

**Week 19: Testing & QA**
1. Write integration tests
2. Write end-to-end tests
3. Test with real immigration cases (anonymized)
4. Performance testing (load testing)
5. Fix bugs and issues

**Week 20: Documentation & Launch Prep**
1. Write API documentation (OpenAPI/Swagger)
2. Write user documentation
3. Write deployment guide
4. Prepare launch materials
5. Soft launch with beta users

## 10.4 Suggested Folder/Repo Structure

```
immigration-platform/
├── backend/
│   ├── src/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   │   ├── routes.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   ├── cases/
│   │   │   ├── rules/
│   │   │   ├── documents/
│   │   │   ├── ai_reasoning/
│   │   │   ├── ingestion/
│   │   │   ├── reviews/
│   │   │   └── admin/
│   │   ├── shared/
│   │   │   ├── database/
│   │   │   ├── security/
│   │   │   └── utils/
│   │   └── main.py
│   ├── migrations/
│   │   └── versions/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
├── ingestion-service/
│   ├── src/
│   │   ├── scheduler/
│   │   ├── fetcher/
│   │   ├── parser/
│   │   └── publisher/
│   └── requirements.txt
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml
│   ├── kubernetes/
│   └── terraform/
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
└── README.md
```

## 10.5 CI/CD Recommendations

### Continuous Integration

1. **On Every Pull Request**:
   - Run linter (flake8/ESLint)
   - Run unit tests
   - Run integration tests
   - Check code coverage (minimum 80%)
   - Run security scan (Snyk, OWASP)

2. **On Merge to Main**:
   - Run all tests
   - Build Docker images
   - Push to container registry
   - Run database migrations in staging
   - Deploy to staging environment

### Continuous Deployment

1. **Staging Environment**:
   - Auto-deploy on merge to main
   - Run smoke tests after deployment
   - Manual approval for production

2. **Production Environment**:
   - Deploy on manual trigger or scheduled release
   - Run database migrations (with backup)
   - Blue-green deployment or rolling update
   - Monitor for errors after deployment

## 10.6 Testing Strategies

### Unit Tests
- Test each function/module in isolation
- Mock external dependencies (DB, LLM, S3)
- Target: 80%+ code coverage
- Run on every commit

### Integration Tests
- Test API endpoints with test database
- Test database operations
- Test service integrations (rule engine + AI)
- Run on every PR

### End-to-End Tests
- Test complete user workflows:
  - User registration → Case creation → Fact submission → Eligibility check → Document upload
- Use test data (anonymized real cases)
- Run before production deployment

### Regression Tests
- Test rule changes don't break existing cases
- Test API backward compatibility
- Run weekly

### QA with Real Cases
- Use anonymized real immigration cases
- Verify eligibility outcomes match expected results
- Test edge cases (borderline salaries, missing docs, etc.)

---

# Section 11: Example Code Snippets / Pseudocode

## 11.1 Database Migrations

### Step-by-Step Implementation

1. **Use Migration Tool**:
   - Use Alembic (Python) or similar migration tool
   - Create migration files for each schema change
   - Version control all migrations

2. **Initial Migration**:
   - Create all tables as defined in Section 3
   - Add all indexes
   - Add all foreign key constraints
   - Add check constraints for enums

3. **Migration Best Practices**:
   - Never modify existing migrations (create new ones)
   - Always test migrations on staging first
   - Backup database before running migrations in production
   - Make migrations reversible (down migration)

## 11.2 API Controllers / Service Functions

### Step-by-Step Implementation

1. **Controller Layer**:
   - Handle HTTP requests/responses
   - Validate input (use Pydantic/similar)
   - Call service layer
   - Return formatted responses

2. **Service Layer**:
   - Contain business logic
   - Call database layer
   - Call external services (LLM, OCR, etc.)
   - Handle errors and edge cases

3. **Database Layer**:
   - Use ORM (SQLAlchemy, TypeORM) or raw SQL
   - Handle transactions
   - Handle connection pooling

## 11.3 Rule Engine Evaluation

### Step-by-Step Implementation

1. **Load Case Facts**:
   - Query `case_facts` table for given case_id
   - Convert to flat dictionary (fact_key → fact_value)
   - Handle duplicate keys (use latest by created_at)

2. **Load Active Rule Version**:
   - Query `visa_rule_versions` with effective date filter
   - Handle multiple active versions (use most recent)
   - Handle missing rule version (return error)

3. **Evaluate Each Requirement**:
   - Load `visa_requirements` for rule version
   - For each requirement:
     - Parse JSON Logic expression
     - Evaluate against case facts
     - Detect missing variables
     - Return pass/fail/missing result

4. **Aggregate Results**:
   - Count passed/failed/missing requirements
   - Compute confidence score (passed / total)
   - Map to outcome (likely/possible/unlikely)
   - Return detailed results

## 11.4 AI Reasoning Orchestration

### Step-by-Step Implementation

1. **Retrieve Context**:
   - Construct query from case facts and visa type
   - Query pgvector with filters (visa_code, effective_date)
   - Retrieve top 5-10 relevant chunks
   - Extract metadata (source_url, document_version_id)

2. **Construct Prompt**:
   - Include case facts (JSON)
   - Include rule evaluation results
   - Include retrieved context chunks
   - Include system instructions (no legal advice, cite sources)

3. **Call LLM**:
   - Use LLM API (OpenAI, Anthropic)
   - Set low temperature (0.1) for consistency
   - Set max tokens (2000)
   - Handle timeouts and retries

4. **Parse Response**:
   - Parse JSON response
   - Validate structure
   - Extract citations
   - Extract confidence score

5. **Store Results**:
   - Store in `ai_reasoning_logs`
   - Store citations in `ai_citations`
   - Link to `document_versions`

## 11.5 Scraper & Ingestion Pipelines

### Step-by-Step Implementation

1. **Scheduler**:
   - Use Airflow or Celery Beat
   - Schedule tasks based on `data_sources.crawl_frequency`
   - Handle task failures and retries

2. **Fetcher**:
   - Make HTTP request to source URL
   - Handle redirects
   - Respect rate limits (1 request per 2 seconds)
   - Handle errors (404, 403, timeout)

3. **Change Detection**:
   - Compute SHA-256 hash of content
   - Compare with last stored hash
   - If different: create new `document_version`
   - If same: skip processing

4. **Diff Engine**:
   - Compare old vs new text
   - Generate unified diff
   - Classify change type
   - Store in `document_diffs`

5. **Rule Parser**:
   - Call LLM to extract rules
   - Parse JSON response
   - Validate extracted logic
   - Store in `parsed_rules` with status='pending'

6. **Publisher**:
   - On approval: create `visa_rule_versions`
   - Create `visa_requirements`
   - Close previous version
   - Update pgvector

## 11.6 Human Review Integration

### Step-by-Step Implementation

1. **Review Creation**:
   - Auto-create on low confidence or conflict
   - User-requested via API
   - Admin-assigned

2. **Reviewer Assignment**:
   - Query available reviewers
   - Apply assignment strategy (round-robin/workload)
   - Update `reviews.reviewer_id`
   - Notify reviewer

3. **Override Creation**:
   - Validate reviewer has permission
   - Create `decision_overrides` entry
   - Preserve original result
   - Update case status
   - Log audit event

## 11.7 Error Handling

### Step-by-Step Implementation

1. **Error Types**:
   - Validation errors (400 Bad Request)
   - Authentication errors (401 Unauthorized)
   - Authorization errors (403 Forbidden)
   - Not found errors (404 Not Found)
   - Business logic errors (409 Conflict)
   - Server errors (500 Internal Server Error)
   - Service unavailable (503 Service Unavailable)

2. **Error Response Format**:
   - Consistent JSON structure
   - Include error code, message, details
   - Include request ID for tracing
   - Include timestamp

3. **Error Logging**:
   - Log all errors with context
   - Include stack trace for server errors
   - Alert on repeated errors
   - Never expose sensitive data in error messages

---

# Section 12: Phased Roadmap

## 12.1 MVP Scope

### Core Features (Must Have)
- User registration and authentication
- Case creation and fact collection
- Basic eligibility check (rule engine only, no AI initially)
- Document upload and basic validation
- Human review request (manual, not auto-escalation)
- Admin rule management (manual, not ingestion)

### Out of Scope for MVP
- Automated ingestion service (use manual rule entry)
- AI reasoning (use rule engine only)
- pgvector (add in Phase 2)
- Auto-escalation to human review
- Multi-jurisdiction support (UK only)

## 12.2 Phase 2 Features

### AI Integration
- Implement RAG retrieval
- Implement LLM reasoning
- Implement citation extraction
- Implement confidence scoring
- Implement auto-escalation

### Ingestion Service
- Implement scraper
- Implement change detection
- Implement rule parsing
- Implement validation workflow
- Implement rule publishing

### Enhanced Documents
- Advanced OCR validation
- Content-based document checks
- Document expiry validation

## 12.3 Phase 3: Multi-Jurisdiction

### Canada Support
- Add Canada jurisdiction to database
- Ingest Canada immigration rules
- Adapt rule engine for Canada-specific logic
- Test with Canada cases

### Australia Support
- Similar to Canada

### EU Blue Card
- Similar approach

## 12.4 Enterprise Integrations

### API Access
- Implement API key authentication
- Implement rate limiting per API key
- Implement webhooks for case status changes
- Provide API documentation

### White-Label
- Customizable branding
- Custom domain support
- Partner-specific rule sets

### Analytics Dashboard
- Case success rates
- Common rejection reasons
- Rule change impact analysis

## 12.5 Scaling Considerations

### pgvector Scaling
- pgvector scales with PostgreSQL (no separate service needed)
- For extreme scale (>100M vectors), consider PostgreSQL read replicas or sharding
- Alternative: Separate vector database (Pinecone, Weaviate) only if needed for extreme scale
- Implement chunking strategy for large documents
- Cache frequently accessed embeddings

### AI Call Optimization
- Cache LLM responses for similar cases
- Batch process eligibility checks
- Use cheaper models for simple cases (GPT-3.5 for simple, GPT-4 for complex)

### Database Scaling
- Implement read replicas for read-heavy queries
- Partition large tables (audit_logs by date)
- Implement connection pooling
- Optimize slow queries

### Concurrent Users
- Horizontal scaling (multiple API servers)
- Load balancing
- Rate limiting per user
- Queue system for heavy operations (eligibility checks)

## 12.6 Monitoring and Maintenance Plan

### Monitoring
- Application metrics (response times, error rates)
- Database metrics (query performance, connection pool)
- AI service metrics (LLM call latency, costs)
- Business metrics (cases created, eligibility outcomes)

### Alerting
- Alert on high error rates (>5% errors)
- Alert on slow response times (>2s p95)
- Alert on service downtime
- Alert on ingestion failures

### Maintenance
- Weekly: Review error logs, check ingestion status
- Monthly: Review performance metrics, optimize slow queries
- Quarterly: Security audit, dependency updates
- Annually: Key rotation, compliance review

---

# Section 13: Developer Notes

## 13.1 Best Practices

1. **Code Organization**:
   - Follow single responsibility principle
   - Use dependency injection
   - Keep functions small and testable
   - Document complex logic

2. **Database**:
   - Always use transactions for multi-step operations
   - Use parameterized queries (prevent SQL injection)
   - Index frequently queried columns
   - Never delete data (soft delete or archive)

3. **API Design**:
   - Use RESTful conventions
   - Version APIs (/api/v1/)
   - Return consistent response formats
   - Handle errors gracefully

4. **Security**:
   - Never log sensitive data (passwords, PII)
   - Validate all inputs
   - Use prepared statements for SQL
   - Encrypt sensitive data at rest

5. **Testing**:
   - Write tests before fixing bugs (TDD)
   - Test edge cases
   - Mock external services
   - Maintain high test coverage

## 13.2 Known Risks / Pitfalls

1. **Rule Conflicts**:
   - Risk: Conflicting rule versions active simultaneously
   - Mitigation: Validate no overlapping effective dates, use most recent

2. **AI Hallucinations**:
   - Risk: LLM makes up citations or rules
   - Mitigation: Only use citations from retrieved context, validate citations exist

3. **Data Loss**:
   - Risk: Accidental deletion of cases or documents
   - Mitigation: Soft delete, regular backups, audit logs

4. **Performance**:
   - Risk: Slow eligibility checks with many requirements
   - Mitigation: Cache rule versions, optimize queries, use async processing

5. **Cost**:
   - Risk: High LLM API costs
   - Mitigation: Cache responses, use cheaper models when possible, set usage limits

## 13.3 Testing and Validation Recommendations

1. **Unit Tests**:
   - Test rule engine with various fact combinations
   - Test edge cases (missing facts, invalid expressions)
   - Test error handling

2. **Integration Tests**:
   - Test complete eligibility check flow
   - Test document upload and validation
   - Test review and override workflow

3. **End-to-End Tests**:
   - Test complete user journey
   - Test with real anonymized cases
   - Verify outcomes match expected results

4. **Performance Tests**:
   - Load test API endpoints
   - Test concurrent eligibility checks
   - Test database under load

5. **Security Tests**:
   - Penetration testing
   - Test authentication/authorization
   - Test input validation
   - Test SQL injection prevention

## 13.4 Recommendations for Iterative Improvements

1. **User Feedback Loop**:
   - Collect user feedback on eligibility outcomes
   - Track cases that went to review
   - Analyze common issues
   - Improve AI prompts based on feedback

2. **Rule Engine Improvements**:
   - Add more operators to JSON Logic
   - Support complex nested conditions
   - Add rule testing framework

3. **AI Improvements**:
   - Fine-tune LLM on immigration domain
   - Improve citation accuracy
   - Reduce hallucinations
   - Improve confidence scoring

4. **Ingestion Improvements**:
   - Improve rule extraction accuracy
   - Reduce false positives in change detection
   - Automate more of validation process

## 13.5 Recommendations for Handling Regulatory Changes

1. **Rule Versioning**:
   - Always version rules (never overwrite)
   - Track effective dates accurately
   - Support retrospective evaluation (evaluate case against rule at time of submission)

2. **Change Detection**:
   - Monitor sources frequently (daily for critical sources)
   - Alert immediately on threshold/fee changes
   - Prioritize urgent changes (2-day SLA)

3. **Validation Process**:
   - Require human validation for all rule changes
   - Maintain audit trail of who approved changes
   - Support rollback if change is incorrect

4. **User Communication**:
   - Notify users when rules change for their visa type
   - Show rule version used for their eligibility check
   - Allow users to re-check with new rules

5. **Compliance**:
   - Regular compliance audits
   - Document all rule sources
   - Maintain legal review process
   - Keep disclaimers up to date

---

# Conclusion

This implementation plan provides a complete, developer-ready guide for building the Immigration Intelligence Platform. 
Every component, workflow, edge case, and compliance requirement has been documented with step-by-step instructions.

The system is designed to be:
- **Scalable**: Architecture supports growth from MVP to enterprise
- **Secure**: Built-in security, GDPR compliance, audit trails
- **Explainable**: Every AI decision is traceable to sources
- **Compliant**: OISC boundary compliance, human-in-loop, versioned rules
- **Maintainable**: Clear module boundaries, comprehensive testing, monitoring

Follow this plan section by section, and you will have a production-ready immigration intelligence platform that 
can scale globally while maintaining regulatory compliance and user trust.

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Implementation
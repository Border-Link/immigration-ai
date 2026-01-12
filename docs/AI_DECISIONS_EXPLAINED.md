# What is AI Decisions?

## Overview

**AI Decisions** is a module that uses **Artificial Intelligence (AI) + Rule Engine** to automatically evaluate immigration case eligibility. It provides intelligent, automated decision-making support for immigration cases.

---

## What Does "AI Decision" Mean?

An **AI Decision** is the result of combining:
1. **Rule Engine Evaluation** - Structured, deterministic rules (JSON Logic)
2. **AI Reasoning (RAG)** - Large Language Model (LLM) that provides nuanced interpretation using Retrieval-Augmented Generation

Together, they produce an **Eligibility Result** that tells you:
- Is the applicant **eligible**, **not eligible**, or **requires review**?
- What's the **confidence level** (0.0 to 1.0)?
- What **reasoning** led to this conclusion?
- What **facts are missing**?

---

## How It Works

### Step 1: Eligibility Check is Triggered

**Automatic Triggers** (System handles this):
- When case is submitted
- When documents are processed and verified
- When payment is completed
- Other system events

**Manual Triggers** (Reviewers/Admins only):
```
POST /api/v1/cases/{case_id}/eligibility
```

**Note**: Regular users **cannot** manually request eligibility checks. The system automatically triggers checks at appropriate times. Only reviewers and admins can manually request checks for review purposes.

### Step 2: Automated Process Runs

The system automatically:

1. **Rule Engine Evaluation**
   - Loads case facts (age, salary, nationality, etc.)
   - Evaluates visa requirements using JSON Logic rules
   - Returns: outcome, confidence, requirements passed/failed

2. **AI Reasoning (RAG)**
   - Searches knowledge base for relevant immigration rules
   - Uses LLM (GPT-4) to provide nuanced interpretation
   - Returns: AI response, citations, reasoning

3. **Combine Outcomes**
   - Detects conflicts between rule engine and AI
   - Resolves conflicts (conservative approach)
   - Calculates final confidence score

4. **Store Eligibility Result** ⭐ **AUTOMATICALLY CREATED HERE**
   - Creates `EligibilityResult` record in database
   - Stores `AIReasoningLog` (prompt, response, tokens used)
   - Stores `AICitation` records (sources used)

5. **Auto-Escalate** (if needed)
   - Low confidence (< 0.6) → Human review
   - Conflicts detected → Human review
   - Missing critical facts → Human review

### Step 3: User Views Results

Users can then:
- View eligibility results: `GET /api/v1/ai-decisions/eligibility-results/`
- Get detailed explanation: `GET /api/v1/cases/{case_id}/eligibility/{result_id}/explanation`
- Update/Delete their own results (if needed)

---

## Why Users Cannot Create Eligibility Results Manually

### ❌ **Security Risk**
- Users could create fake eligibility results with arbitrary outcomes
- Users could set false confidence scores
- Users could bypass the payment requirement
- Users could manipulate the system

### ❌ **Data Integrity**
- Eligibility results must be based on actual rule evaluation and AI reasoning
- Manual creation would break the audit trail
- Manual creation would not have proper citations or reasoning logs

### ❌ **Business Logic**
- Eligibility results are the **output** of a complex evaluation process
- They require:
  - Rule engine evaluation
  - AI reasoning with context retrieval
  - Conflict detection and resolution
  - Proper citations and audit logs

### ✅ **Correct Flow**
1. User requests eligibility check → `POST /api/v1/cases/{case_id}/eligibility`
2. System automatically runs evaluation
3. System automatically creates eligibility result
4. User views the result

---

## What Users CAN Do

### ✅ **View Eligibility Results** (After Automatic Check)
- Eligibility checks are automatically triggered by the system
- Users can view results after the automatic check completes

### ✅ **View Eligibility Results**
- `GET /api/v1/ai-decisions/eligibility-results/` - List their results
- `GET /api/v1/ai-decisions/eligibility-results/{id}/` - View specific result
- `GET /api/v1/cases/{case_id}/eligibility/{result_id}/explanation` - Get detailed explanation

### ✅ **Update/Delete Their Own Results**
- `PATCH /api/v1/ai-decisions/eligibility-results/{id}/update/` - Update (e.g., add notes)
- `DELETE /api/v1/ai-decisions/eligibility-results/{id}/delete/` - Delete (e.g., clear old results)

**Note**: Update/Delete are for user convenience (e.g., clearing old results before running a new check), but the **creation** is always automatic.

---

## What Reviewers Can Do

### ✅ **View AI Reasoning Logs**
- `GET /api/v1/ai-decisions/ai-reasoning-logs/` - List all AI reasoning logs
- `GET /api/v1/ai-decisions/ai-reasoning-logs/{id}/` - View specific log (prompt, response, tokens)

**Purpose**: Reviewers need to audit AI decisions, debug issues, and ensure quality.

### ✅ **View AI Citations**
- `GET /api/v1/ai-decisions/ai-citations/` - List all citations
- `GET /api/v1/ai-decisions/ai-citations/{id}/` - View specific citation

**Purpose**: Reviewers need to verify that AI is citing correct sources and using accurate information.

---

## What Admins Can Do

### ✅ **Full Management**
- All reviewer capabilities
- Advanced filtering and analytics
- Bulk operations
- Data cleanup and maintenance

---

## Key Components

### 1. **EligibilityResult**
- The final outcome (eligible/not eligible/requires review)
- Confidence score
- Reasoning summary
- Missing facts

### 2. **AIReasoningLog**
- The prompt sent to the LLM
- The response received
- Model used (e.g., GPT-4)
- Tokens consumed
- Timestamp

### 3. **AICitation**
- Source documents used by AI
- Excerpts from documents
- Relevance scores
- Links to document versions

---

## Example Flow

```
System Event: Case submitted / Documents verified / Payment completed
    ↓
System: AUTOMATICALLY TRIGGERS eligibility check
    ↓
System: Runs rule engine evaluation
    ↓
System: Runs AI reasoning (RAG)
    ↓
System: Combines outcomes
    ↓
System: AUTOMATICALLY CREATES EligibilityResult
    ↓
System: Stores AIReasoningLog and AICitations
    ↓
User: Views result via GET /api/v1/ai-decisions/eligibility-results/
```

**Alternative Flow (Reviewer/Admin Manual Request)**:
```
Reviewer/Admin: POST /api/v1/cases/123/eligibility
    ↓
System: Runs rule engine evaluation
    ↓
System: Runs AI reasoning (RAG)
    ↓
System: AUTOMATICALLY CREATES EligibilityResult
    ↓
Reviewer/Admin: Views result
```

---

## Summary

- **AI Decisions** = Automated eligibility evaluation using AI + Rule Engine
- **Eligibility Results** = Output of the evaluation (automatically created)
- **Users** = View results (cannot request checks manually - checks are automatic)
- **Reviewers** = Can manually request checks for review, audit AI decisions, view reasoning logs
- **Admins** = Can manually request checks, full management capabilities

**Key Principles**:
1. Eligibility results are **automatically generated** by the system, not manually created by users
2. Eligibility checks are **automatically triggered** by system events (case submission, document processing, payment completion)
3. Regular users **cannot** manually request eligibility checks (prevents abuse and spam)
4. Only reviewers and admins can manually request eligibility checks for review purposes

This ensures data integrity, security, proper audit trails, and prevents system abuse.

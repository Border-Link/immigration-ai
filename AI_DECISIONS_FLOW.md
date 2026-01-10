# AI Decisions Directory - Complete Flow Documentation

## Overview

The `ai_decisions` directory implements the AI reasoning and eligibility checking system using a hybrid approach: **Rule Engine + AI Reasoning (RAG)**. This document explains the architecture and complete flow.

---

## Why Separate Services?

### 1. **PgVectorService (vector_db_service.py)** - Vector Storage & Search
**Purpose**: Handles storing and querying document chunks with embeddings in PostgreSQL using pgvector extension.

**Responsibilities**:
- Store document chunks with embeddings in PostgreSQL
- Search for similar chunks using cosine similarity
- Manage chunks (get, delete, update by document version)
- Filter by metadata (visa_code, jurisdiction, etc.)

**Why Separate?**
- **Single Responsibility**: Only handles vector operations (storage/retrieval)
- **Database Abstraction**: Encapsulates pgvector-specific operations
- **Reusability**: Can be used by other services that need vector search
- **Testability**: Can be tested independently

### 2. **EmbeddingService** - Embedding Generation
**Purpose**: Handles text chunking and embedding generation using OpenAI API.

**Responsibilities**:
- Split documents into chunks (with overlap)
- Generate embeddings using OpenAI API
- Validate embedding dimensions
- Handle chunking strategies

**Why Separate?**
- **Single Responsibility**: Only handles embedding generation
- **API Abstraction**: Encapsulates OpenAI API calls
- **Flexibility**: Can swap embedding providers without changing storage logic
- **Testability**: Can be mocked for testing

**Key Insight**: These services follow the **Single Responsibility Principle**. They could be combined, but separation provides:
- Better maintainability
- Easier testing
- Clearer code organization
- Ability to swap implementations independently

---

## Complete Flow: From API Call to Result

### Flow Diagram

```
API Request
    ↓
POST /api/v1/cases/{case_id}/eligibility
    ↓
CaseEligibilityCheckAPI.post()
    ↓
EligibilityCheckService.run_eligibility_check()
    ├──→ Rule Engine Evaluation
    │       └──→ RuleEngineService.run_eligibility_evaluation()
    │           ├──→ Load case facts
    │           ├──→ Load active rule version
    │           ├──→ Evaluate requirements (JSON Logic)
    │           └──→ Aggregate results
    │
    └──→ AI Reasoning (RAG)
            └──→ AIReasoningService.run_ai_reasoning()
                ├──→ Step 1: Retrieve Context
                │       ├──→ EmbeddingService.generate_embedding(query)
                │       └──→ PgVectorService.search_similar()
                │           └──→ PostgreSQL pgvector cosine similarity search
                │
                ├──→ Step 2: Construct Prompt
                │       └──→ AIReasoningService.construct_prompt()
                │           └──→ Combine context + rule results + case facts
                │
                ├──→ Step 3: Call LLM
                │       └──→ AIReasoningService.call_llm()
                │           └──→ OpenAI API (gpt-4)
                │
                └──→ Step 4: Store Results
                        ├──→ AIReasoningLogService.create_reasoning_log()
                        └──→ AICitationService.create_citation()
                            └──→ Link citations to document versions
    ↓
EligibilityCheckService._combine_outcomes()
    ├──→ Detect conflicts (rule vs AI)
    ├──→ Resolve conflicts (conservative approach)
    └──→ Calculate final confidence
    ↓
EligibilityCheckService._store_eligibility_result()
    └──→ EligibilityResultService.create_eligibility_result()
    ↓
EligibilityCheckService._escalate_to_human_review() (if needed)
    └──→ ReviewService.create_review()
    ↓
Update Case Status → 'evaluated'
    ↓
API Response
```

---

## Detailed Step-by-Step Flow

### Step 1: API Request
**Endpoint**: `POST /api/v1/cases/{case_id}/eligibility`

**Location**: `src/immigration_cases/views/case/eligibility.py`

**What Happens**:
1. Validate case exists
2. Check permissions (user owns case OR reviewer/admin)
3. Get visa types (from request or all active for jurisdiction)
4. Call `EligibilityCheckService.run_eligibility_check()` for each visa type

---

### Step 2: Eligibility Check Orchestration
**Service**: `EligibilityCheckService.run_eligibility_check()`

**Location**: `src/ai_decisions/services/eligibility_check_service.py`

**What Happens**:
1. **Load Prerequisites**:
   - Load case facts
   - Load active rule version for visa type
   - Load visa type details

2. **Run Rule Engine**:
   - Call `RuleEngineService.run_eligibility_evaluation()`
   - Evaluates all requirements using JSON Logic
   - Returns: outcome, confidence, requirements_passed, missing_facts

3. **Run AI Reasoning** (if enabled):
   - Call `AIReasoningService.run_ai_reasoning()`
   - Returns: AI response, context chunks, citations

4. **Combine Outcomes**:
   - Detect conflicts between rule engine and AI
   - Resolve conflicts (conservative: use "possible" outcome)
   - Calculate final confidence
   - Determine if human review needed

5. **Store Results**:
   - Store `EligibilityResult` in database
   - Store `AIReasoningLog` (if AI reasoning ran)
   - Store `AICitation` records

6. **Auto-Escalate** (if needed):
   - If confidence < 0.6 → escalate to human review
   - If conflict detected → escalate to human review
   - If missing critical facts → escalate to human review

---

### Step 3: Rule Engine Evaluation
**Service**: `RuleEngineService.run_eligibility_evaluation()`

**Location**: `src/rules_knowledge/services/rule_engine_service.py`

**What Happens**:
1. Load case facts (from `case_facts` table)
2. Load active rule version (filtered by effective dates)
3. Evaluate each requirement:
   - Extract JSON Logic expression
   - Substitute case facts into expression
   - Evaluate using `json-logic-py`
   - Determine pass/fail
4. Aggregate results:
   - Count passed/failed requirements
   - Calculate overall outcome (likely/possible/unlikely)
   - Calculate confidence score
   - Identify missing facts

**Returns**: `RuleEngineEvaluationResult` with outcome, confidence, requirements details

---

### Step 4: AI Reasoning (RAG Workflow)
**Service**: `AIReasoningService.run_ai_reasoning()`

**Location**: `src/ai_decisions/services/ai_reasoning_service.py`

#### 4.1: Retrieve Context (Vector Search)

**What Happens**:
1. **Construct Query**:
   - Build query text from case facts
   - Include key fields: salary, age, education, visa_type, etc.

2. **Generate Query Embedding**:
   ```python
   EmbeddingService.generate_embedding(query_text)
   ```
   - Calls OpenAI API: `text-embedding-ada-002`
   - Returns: 1536-dimensional vector

3. **Search Similar Chunks**:
   ```python
   PgVectorService.search_similar(
       query_embedding=embedding,
       filters={'visa_code': 'SKILLED_WORKER'},
       similarity_threshold=0.7
   )
   ```
   - Uses PostgreSQL pgvector extension
   - Cosine similarity search on `document_chunks.embedding` column
   - Filters by metadata (visa_code, jurisdiction)
   - Returns: Top 5 most similar chunks

4. **Format Context**:
   - Extract chunk text, source URL, metadata
   - Calculate similarity scores
   - Include chunk_id for citation mapping

**Why PgVectorService?**
- Encapsulates pgvector-specific operations
- Handles cosine distance calculations
- Manages metadata filtering
- Provides clean abstraction over PostgreSQL vector operations

#### 4.2: Construct Prompt

**What Happens**:
1. Combine:
   - System instruction (role as immigration advisor)
   - Retrieved context chunks (with similarity scores)
   - Rule engine evaluation results
   - Case facts
2. Format as structured prompt for LLM

#### 4.3: Call LLM

**What Happens**:
1. Call OpenAI API:
   ```python
   OpenAI().chat.completions.create(
       model="gpt-4",
       messages=[...],
       temperature=0.3  # Deterministic
   )
   ```
2. Extract response text
3. Extract citations from response (URLs, context references)
4. Track token usage

#### 4.4: Store Reasoning & Citations

**What Happens**:
1. **Store Reasoning Log**:
   ```python
   AIReasoningLogService.create_reasoning_log(
       case_id=case_id,
       prompt=prompt,
       response=llm_response,
       model_name="gpt-4"
   )
   ```
   - Stores in `ai_reasoning_logs` table

2. **Store Citations**:
   ```python
   AICitationService.create_citation(
       reasoning_log_id=log_id,
       document_version_id=doc_version_id,
       excerpt=chunk_text,
       relevance_score=similarity
   )
   ```
   - Maps context chunks to document versions
   - Stores excerpt and relevance score
   - Links to reasoning log for traceability

**Why Separate Services?**
- **AIReasoningLogService**: Handles reasoning log CRUD operations
- **AICitationService**: Handles citation CRUD operations
- **PgVectorService**: Handles vector search (used by AIReasoningService)
- **EmbeddingService**: Handles embedding generation (used by AIReasoningService)

Each service has a single, clear responsibility.

---

### Step 5: Combine Outcomes

**Service**: `EligibilityCheckService._combine_outcomes()`

**What Happens**:
1. **Start with Rule Engine Result**:
   - Outcome: likely/possible/unlikely
   - Confidence: 0.0 to 1.0

2. **If AI Reasoning Available**:
   - Extract AI outcome from response (heuristic parsing)
   - Extract AI confidence from response
   - Check for conflicts:
     - Rule: "likely" + AI: "unlikely" → **CONFLICT**
     - Rule: "unlikely" + AI: "likely" → **CONFLICT**

3. **Resolve Conflicts**:
   - Use conservative approach: "possible" outcome
   - Lower confidence (min of rule and AI)
   - Flag for human review

4. **If No Conflict**:
   - Use AI outcome (AI provides nuance)
   - Use AI confidence
   - Use AI reasoning summary

5. **Check Low Confidence**:
   - If confidence < 0.6 → flag for human review

6. **Check Missing Facts**:
   - If critical facts missing → flag for human review

**Returns**: Combined outcome, confidence, reasoning_summary, requires_human_review

---

### Step 6: Store Eligibility Result

**Service**: `EligibilityCheckService._store_eligibility_result()`

**What Happens**:
1. Map implementation.md outcomes to model choices:
   - "likely" → "eligible"
   - "possible" → "requires_review"
   - "unlikely" → "not_eligible"

2. Create `EligibilityResult`:
   ```python
   EligibilityResultService.create_eligibility_result(
       case_id=case_id,
       visa_type_id=visa_type_id,
       rule_version_id=rule_version_id,
       outcome="eligible",  # Mapped from "likely"
       confidence=0.92,
       reasoning_summary="...",
       missing_facts=["sponsor_license"]
   )
   ```

3. Store in `eligibility_results` table

---

### Step 7: Auto-Escalate to Human Review

**Service**: `EligibilityCheckService._escalate_to_human_review()`

**What Happens** (if conditions met):
1. Create review record:
   ```python
   ReviewService.create_review(
       case_id=case_id,
       auto_assign=True
   )
   ```
2. Update case status to "awaiting_review"
3. Assign reviewer (round-robin or workload-based)

**Conditions for Escalation**:
- Confidence < 0.6 (low confidence)
- Rule-AI conflict detected
- Missing critical facts
- Explicit conflict reason provided

---

### Step 8: Update Case Status

**What Happens**:
1. Update case status to "evaluated"
2. Case is now ready for user to view results

---

### Step 9: API Response

**Response Format** (matches implementation.md):
```json
{
  "case_id": "...",
  "results": [
    {
      "visa_code": "SKILLED_WORKER",
      "visa_name": "Skilled Worker Visa",
      "outcome": "likely",
      "confidence": 0.92,
      "rule_version_id": "...",
      "requirements_passed": 8,
      "requirements_total": 10,
      "missing_requirements": [...],
      "citations": [...],
      "reasoning_summary": "..."
    }
  ],
  "requires_human_review": false,
  "low_confidence_flags": [],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

## Service Responsibilities Summary

| Service | Responsibility | Used By |
|---------|---------------|---------|
| **EligibilityCheckService** | Orchestrates complete eligibility check flow | API Views, Celery Tasks |
| **AIReasoningService** | RAG workflow (retrieve, prompt, LLM, store) | EligibilityCheckService |
| **RuleEngineService** | Evaluate JSON Logic requirements | EligibilityCheckService |
| **PgVectorService** | Vector storage & similarity search | AIReasoningService, RulePublishingService |
| **EmbeddingService** | Generate embeddings & chunk documents | AIReasoningService, RulePublishingService |
| **EligibilityResultService** | CRUD for eligibility results | EligibilityCheckService, API Views |
| **AIReasoningLogService** | CRUD for reasoning logs | AIReasoningService |
| **AICitationService** | CRUD for citations | AIReasoningService |

---

## Key Design Decisions

### 1. **Why Separate PgVectorService and EmbeddingService?**
- **Separation of Concerns**: Storage vs. Generation
- **Testability**: Can mock embedding generation without database
- **Flexibility**: Can swap embedding provider without changing storage
- **Reusability**: Other services can use vector search independently

### 2. **Why Separate AIReasoningService from EligibilityCheckService?**
- **Single Responsibility**: AI reasoning is a distinct workflow
- **Reusability**: Can be used independently for other AI tasks
- **Testability**: Can test RAG workflow in isolation

### 3. **Why Stateless Services?**
- **Thread Safety**: No shared state
- **Scalability**: Can run in parallel
- **Testability**: Easier to test without setup/teardown

### 4. **Why pgvector Instead of Separate Vector DB?**
- **Simplicity**: Single database, no additional infrastructure
- **ACID Compliance**: Transactions work across all data
- **Cost**: No additional service costs
- **Performance**: HNSW index provides fast similarity search

---

## Data Flow Diagram

```
Case Facts (case_facts table)
    ↓
Rule Engine → RuleEngineEvaluationResult
    ↓
AI Reasoning:
    Case Facts → EmbeddingService → Query Embedding
    Query Embedding → PgVectorService → Similar Chunks
    Similar Chunks + Rule Results → AIReasoningService → LLM Prompt
    LLM Prompt → OpenAI API → LLM Response
    LLM Response → AIReasoningLogService → ai_reasoning_logs table
    Similar Chunks → AICitationService → ai_citations table
    ↓
EligibilityCheckService._combine_outcomes()
    ↓
EligibilityResultService → eligibility_results table
    ↓
ReviewService (if needed) → reviews table
    ↓
Case Status → "evaluated"
```

---

## Conclusion

The `ai_decisions` directory implements a **hybrid eligibility checking system** that combines:
1. **Deterministic Rule Engine** (JSON Logic) - Fast, reliable, explainable
2. **AI Reasoning (RAG)** - Nuanced interpretation, context-aware

The separation of services follows **SOLID principles**:
- **Single Responsibility**: Each service has one clear purpose
- **Open/Closed**: Can extend without modifying existing code
- **Dependency Inversion**: Services depend on abstractions, not implementations

This architecture provides:
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Testability**: Each service can be tested independently
- ✅ **Scalability**: Stateless services can scale horizontally
- ✅ **Flexibility**: Can swap implementations without breaking other services

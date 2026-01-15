"""
Pytest configuration and shared fixtures for data_ingestion tests.

Conventions (aligned with users_access):
- Prefer exercising business logic through services.
- Avoid direct model calls in tests; use services/repositories for setup only when a service create API does not exist.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Dict, List
import pytest
from main_system.utils.cache_utils import cache_clear
from rest_framework.test import APIClient
from users_access.services.user_service import UserService
from data_ingestion.services.data_source_service import DataSourceService
from data_ingestion.services.source_document_service import SourceDocumentService
from data_ingestion.services.document_version_service import DocumentVersionService
from data_ingestion.services.document_diff_service import DocumentDiffService
from data_ingestion.services.parsed_rule_service import ParsedRuleService
from data_ingestion.services.rule_validation_task_service import RuleValidationTaskService
from data_ingestion.services.audit_log_service import RuleParsingAuditLogService
from data_ingestion.services.ingestion_service import IngestionService
from data_ingestion.services.rule_parsing.service import RuleParsingService


@pytest.fixture(autouse=True)
def _clear_cache():
    """Avoid cross-test cache coupling due to @cache_result usage."""
    cache_clear()


@pytest.fixture
def api_client():
    """DRF APIClient."""
    return APIClient()


# -----------------------------------------------------------------------------
# Service fixtures (return the class, same pattern as users_access)
# -----------------------------------------------------------------------------

@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def data_source_service():
    return DataSourceService


@pytest.fixture
def source_document_service():
    return SourceDocumentService


@pytest.fixture
def document_version_service():
    return DocumentVersionService


@pytest.fixture
def document_diff_service():
    return DocumentDiffService


@pytest.fixture
def parsed_rule_service():
    return ParsedRuleService


@pytest.fixture
def rule_validation_task_service():
    return RuleValidationTaskService


@pytest.fixture
def audit_log_service():
    return RuleParsingAuditLogService


@pytest.fixture
def ingestion_service():
    return IngestionService


@pytest.fixture
def rule_parsing_service():
    return RuleParsingService


# -----------------------------------------------------------------------------
# User fixtures (permissions: ingestion/admin endpoints require staff/superuser)
# -----------------------------------------------------------------------------

@pytest.fixture
def superadmin_user(user_service):
    """Superuser to satisfy IsSuperAdmin and AdminPermission."""
    email = f"superadmin-{uuid.uuid4().hex[:8]}@example.com"
    return user_service.create_superuser(email=email, password="adminpass123")


@pytest.fixture
def staff_user(user_service):
    """Staff user to satisfy IngestionPermission/AdminPermission."""
    email = f"staff-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="staffpass123")
    user_service.activate_user(user)
    user_service.update_user(user, is_staff=True)
    return user


@pytest.fixture
def reviewer_user(user_service):
    """Reviewer user (may be assigned to validation tasks)."""
    email = f"reviewer-{uuid.uuid4().hex[:8]}@example.com"
    user = user_service.create_user(email=email, password="reviewerpass123")
    user_service.activate_user(user)
    user_service.update_user(user, role="reviewer", is_staff=True)
    return user


# -----------------------------------------------------------------------------
# Domain object fixtures (created through services when available)
# -----------------------------------------------------------------------------

@pytest.fixture
def uk_data_source(data_source_service):
    """A minimal UK data source."""
    name = f"UK Source {uuid.uuid4().hex[:6]}"
    return data_source_service.create_data_source(
        name=name,
        base_url="https://www.gov.uk/api/content/entering-staying-uk",
        jurisdiction="UK",
        crawl_frequency="weekly",
        is_active=True,
    )


@pytest.fixture
def source_document(uk_data_source):
    """Create a SourceDocument via repository (no service create API exists)."""
    from data_ingestion.repositories.source_document_repository import SourceDocumentRepository

    return SourceDocumentRepository.create_source_document(
        data_source=uk_data_source,
        source_url="https://www.gov.uk/api/content/example",
        raw_content='{"title":"Example","description":"Example description","content_id":"cid"}',
        content_type="application/json",
        http_status_code=200,
    )


@pytest.fixture
def document_version(source_document):
    """Create a DocumentVersion via repository (no service create API exists)."""
    from data_ingestion.repositories.document_version_repository import DocumentVersionRepository

    return DocumentVersionRepository.create_document_version(
        source_document=source_document,
        raw_text="Title: Example\nDescription: Example description\nFee is £100\n",
        metadata={"content_id": "cid", "base_path": "/example"},
    )


@pytest.fixture
def second_document_version(source_document):
    """A distinct document version for diffing/filters."""
    from data_ingestion.repositories.document_version_repository import DocumentVersionRepository

    return DocumentVersionRepository.create_document_version(
        source_document=source_document,
        raw_text="Title: Example\nDescription: Updated description\nFee is £200\n",
        metadata={"content_id": "cid", "base_path": "/example"},
    )


@pytest.fixture
def document_diff(document_version, second_document_version):
    """Create a DocumentDiff via repository (no service create API exists)."""
    from data_ingestion.repositories.document_diff_repository import DocumentDiffRepository

    return DocumentDiffRepository.create_document_diff(
        old_version=document_version,
        new_version=second_document_version,
        diff_text="-Fee is £100\n+Fee is £200\n",
        change_type="fee_change",
    )


@pytest.fixture
def parsed_rule(document_version):
    """Create a ParsedRule via repository (no service create API exists)."""
    from data_ingestion.repositories.parsed_rule_repository import ParsedRuleRepository

    return ParsedRuleRepository.create_parsed_rule(
        document_version=document_version,
        visa_code="UK_SKILLED_WORKER",
        rule_type="fee",
        extracted_logic={"==": [{"var": "fee_paid"}, True]},
        description="Applicant must pay the application fee.",
        source_excerpt="Fee is £100",
        confidence_score=0.9,
        status="pending",
        llm_model="test-model",
        tokens_used=10,
        estimated_cost=Decimal("0.000100"),
        processing_time_ms=5,
    )


@pytest.fixture
def validation_task(parsed_rule):
    """Create a RuleValidationTask via repository (no service create API exists)."""
    from django.utils import timezone
    from datetime import timedelta
    from data_ingestion.repositories.rule_validation_task_repository import RuleValidationTaskRepository

    return RuleValidationTaskRepository.create_validation_task(
        parsed_rule=parsed_rule,
        assigned_to=None,
        sla_deadline=timezone.now() + timedelta(days=7),
        status="pending",
    )


@pytest.fixture
def audit_log(document_version, staff_user):
    """Create a rule parsing audit log entry via repository."""
    from data_ingestion.repositories.audit_log_repository import RuleParsingAuditLogRepository

    return RuleParsingAuditLogRepository.create_audit_log(
        document_version=document_version,
        action="parse_started",
        status="success",
        message="Parse started",
        metadata={"test": True},
        user=staff_user,
    )


@pytest.fixture
def document_chunks(document_version) -> List:
    """Create DocumentChunk rows via a service (PgVectorService)."""
    from ai_decisions.services.vector_db_service import PgVectorService

    chunks: List[Dict] = [
        {"text": "Chunk A", "metadata": {"chunk_index": 0, "visa_code": "UK_SKILLED_WORKER"}},
        {"text": "Chunk B", "metadata": {"chunk_index": 1, "visa_code": "UK_SKILLED_WORKER"}},
    ]
    embeddings: List[List[float]] = [[0.0] * 1536, [0.1] * 1536]
    return PgVectorService.store_chunks(document_version=document_version, chunks=chunks, embeddings=embeddings)


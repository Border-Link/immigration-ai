"""
Pytest configuration and shared fixtures for rules_knowledge tests.

Constraints:
- Do not call models directly from tests; use services for setup/actions.
- Keep tests separated by concern: services/ and views/.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from users_access.services.user_service import UserService
from rules_knowledge.services import (
    DocumentTypeService,
    VisaTypeService,
    VisaRuleVersionService,
    VisaRequirementService,
    VisaDocumentRequirementService,
)


@pytest.fixture
def user_service():
    return UserService


@pytest.fixture
def document_type_service():
    return DocumentTypeService


@pytest.fixture
def visa_type_service():
    return VisaTypeService


@pytest.fixture
def visa_rule_version_service():
    return VisaRuleVersionService


@pytest.fixture
def visa_requirement_service():
    return VisaRequirementService


@pytest.fixture
def visa_document_requirement_service():
    return VisaDocumentRequirementService


@pytest.fixture
def regular_user(user_service):
    return user_service.create_user(email="rk-user@example.com", password="testpass123")


@pytest.fixture
def staff_user(user_service):
    user = user_service.create_user(email="rk-staff@example.com", password="testpass123")
    # RulePermission/AdminPermission uses RoleChecker.is_staff(), which accepts is_staff=True
    user_service.update_user(user, is_staff=True)
    return user


@pytest.fixture
def admin_user(user_service):
    return user_service.create_superuser(email="rk-admin@example.com", password="adminpass123")


@pytest.fixture
def document_type(document_type_service):
    return document_type_service.create_document_type(
        code="PASSPORT",
        name="Passport",
        description="Passport document",
        is_active=True,
    )


@pytest.fixture
def inactive_document_type(document_type_service):
    return document_type_service.create_document_type(
        code="BIRTH_CERT",
        name="Birth Certificate",
        description="Birth certificate",
        is_active=False,
    )


@pytest.fixture
def visa_type_uk(visa_type_service):
    return visa_type_service.create_visa_type(
        jurisdiction="UK",
        code="SKILLED_WORKER",
        name="Skilled Worker",
        description="UK skilled worker route",
        is_active=True,
    )


@pytest.fixture
def visa_type_us(visa_type_service):
    return visa_type_service.create_visa_type(
        jurisdiction="US",
        code="H1B",
        name="H-1B",
        description="US H-1B route",
        is_active=True,
    )


@pytest.fixture
def rule_version_unpublished(visa_rule_version_service, visa_type_uk):
    return visa_rule_version_service.create_rule_version(
        visa_type_id=str(visa_type_uk.id),
        effective_from=timezone.now() + timedelta(days=7),
        effective_to=None,
        is_published=False,
        created_by=None,
    )


@pytest.fixture
def rule_version_published_current(visa_rule_version_service, visa_type_uk):
    rule_version = visa_rule_version_service.create_rule_version(
        visa_type_id=str(visa_type_uk.id),
        effective_from=timezone.now() - timedelta(days=1),
        effective_to=None,
        is_published=False,
        created_by=None,
    )
    published = visa_rule_version_service.publish_rule_version(str(rule_version.id))
    return published


@pytest.fixture
def visa_requirement(visa_requirement_service, rule_version_unpublished):
    return visa_requirement_service.create_visa_requirement(
        rule_version_id=str(rule_version_unpublished.id),
        requirement_code="MIN_AGE",
        description="Applicant must be at least 18",
        condition_expression={">=": [{"var": "age"}, 18]},
        is_active=True,
    )


@pytest.fixture
def visa_document_requirement(visa_document_requirement_service, rule_version_unpublished, document_type):
    return visa_document_requirement_service.create_visa_document_requirement(
        rule_version_id=str(rule_version_unpublished.id),
        document_type_id=str(document_type.id),
        mandatory=True,
        description="Passport required",
    )


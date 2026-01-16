"""
Tests for VisaRuleVersionService including optimistic locking.
All tests use services, not direct model access.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestVisaRuleVersionService:
    def test_create_rule_version_success(self, visa_rule_version_service, visa_type_uk):
        rv = visa_rule_version_service.create_rule_version(
            visa_type_id=str(visa_type_uk.id),
            effective_from=timezone.now() + timedelta(days=3),
            effective_to=None,
            is_published=False,
        )
        assert rv is not None
        assert rv.visa_type_id == visa_type_uk.id
        assert rv.is_published is False
        assert rv.is_deleted is False
        assert rv.version == 1

    def test_create_rule_version_invalid_visa_type_returns_none(self, visa_rule_version_service):
        from uuid import uuid4

        rv = visa_rule_version_service.create_rule_version(
            visa_type_id=str(uuid4()),
            effective_from=timezone.now() + timedelta(days=1),
        )
        assert rv is None

    def test_get_all_and_get_by_id(self, visa_rule_version_service, rule_version_unpublished):
        all_qs = visa_rule_version_service.get_all()
        assert all_qs.filter(id=rule_version_unpublished.id).exists() is True

        found = visa_rule_version_service.get_by_id(str(rule_version_unpublished.id))
        assert found is not None
        assert found.id == rule_version_unpublished.id

    def test_get_by_id_not_found_returns_none(self, visa_rule_version_service):
        from uuid import uuid4

        assert visa_rule_version_service.get_by_id(str(uuid4())) is None

    def test_get_by_visa_type(self, visa_rule_version_service, visa_type_uk, rule_version_unpublished):
        qs = visa_rule_version_service.get_by_visa_type(str(visa_type_uk.id))
        assert qs.filter(id=rule_version_unpublished.id).exists() is True

    def test_publish_rule_version_success_and_version_increment(self, visa_rule_version_service, rule_version_unpublished):
        # Unpublished starts at version 1
        assert rule_version_unpublished.version == 1
        published = visa_rule_version_service.publish_rule_version(str(rule_version_unpublished.id), expected_version=1)
        assert published is not None
        assert published.is_published is True
        assert published.version == 2

    def test_publish_rule_version_version_conflict_raises(self, visa_rule_version_service, rule_version_unpublished):
        with pytest.raises(ValidationError):
            visa_rule_version_service.publish_rule_version(str(rule_version_unpublished.id), expected_version=999)

    def test_update_rule_version_success_and_version_increment(self, visa_rule_version_service, rule_version_unpublished):
        updated = visa_rule_version_service.update_rule_version(
            str(rule_version_unpublished.id),
            expected_version=1,
            effective_to=timezone.now() + timedelta(days=30),
        )
        assert updated is not None
        assert updated.version == 2
        assert updated.effective_to is not None

    def test_update_rule_version_version_conflict_raises(self, visa_rule_version_service, rule_version_unpublished):
        with pytest.raises(ValidationError):
            visa_rule_version_service.update_rule_version(
                str(rule_version_unpublished.id),
                expected_version=999,
                effective_to=timezone.now() + timedelta(days=30),
            )

    def test_delete_rule_version_success_and_excluded_from_get(self, visa_rule_version_service, rule_version_unpublished):
        ok = visa_rule_version_service.delete_rule_version(str(rule_version_unpublished.id))
        assert ok is True

        # Service get_by_id excludes soft-deleted
        assert visa_rule_version_service.get_by_id(str(rule_version_unpublished.id)) is None

        # Service get_all excludes soft-deleted
        assert visa_rule_version_service.get_all().filter(id=rule_version_unpublished.id).exists() is False


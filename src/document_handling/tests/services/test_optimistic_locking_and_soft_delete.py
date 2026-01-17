"""
Tests for optimistic locking, race conditions, conflict detection, and soft delete
in document_handling module.

Tests cover:
- Version conflicts on concurrent updates
- Race condition handling
- Soft delete functionality
- Restore functionality
- Selector filtering of soft-deleted records
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from threading import Thread, Barrier
from document_handling.repositories.case_document_repository import CaseDocumentRepository
from document_handling.repositories.document_check_repository import DocumentCheckRepository
from document_handling.models.case_document import CaseDocument
from document_handling.models.document_check import DocumentCheck
from document_handling.selectors.case_document_selector import CaseDocumentSelector
from document_handling.selectors.document_check_selector import DocumentCheckSelector
from document_handling.services.case_document_service import CaseDocumentService
from document_handling.services.document_check_service import DocumentCheckService


@pytest.mark.django_db
class TestCaseDocumentOptimisticLocking:
    """Tests for optimistic locking in CaseDocument."""

    def test_create_case_document_has_version_one(self, case_document):
        """New documents should start with version 1."""
        assert case_document.version == 1
        assert case_document.is_deleted is False
        assert case_document.deleted_at is None

    def test_update_case_document_increments_version(self, case_document):
        """Updating a document should increment its version."""
        initial_version = case_document.version
        
        updated = CaseDocumentRepository.update_case_document(
            case_document,
            version=initial_version,
            file_name="updated.pdf"
        )
        
        assert updated.version == initial_version + 1
        assert updated.file_name == "updated.pdf"

    def test_update_case_document_version_conflict_raises_error(self, case_document):
        """Updating with wrong version should raise ValidationError."""
        initial_version = case_document.version
        
        # First update succeeds
        CaseDocumentRepository.update_case_document(
            case_document,
            version=initial_version,
            file_name="first.pdf"
        )
        
        # Second update with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            CaseDocumentRepository.update_case_document(
                case_document,
                version=initial_version,  # Stale version
                file_name="second.pdf"
            )
        
        assert "modified by another user" in str(exc_info.value).lower()

    def test_update_case_document_missing_version_raises_error(self, case_document):
        """Updating without version should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CaseDocumentRepository.update_case_document(
                case_document,
                # No version parameter
                file_name="updated.pdf"
            )
        
        assert "missing version" in str(exc_info.value).lower()

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_updates_race_condition(self, case_document):
        """Test that concurrent updates are handled correctly."""
        initial_version = case_document.version
        results = []
        errors = []
        barrier = Barrier(2)
        
        def update_document(thread_id):
            try:
                barrier.wait()  # Synchronize threads
                updated = CaseDocumentRepository.update_case_document(
                    case_document,
                    version=initial_version,
                    file_name=f"thread_{thread_id}.pdf"
                )
                results.append((thread_id, updated.version))
            except ValidationError as e:
                errors.append((thread_id, str(e)))
        
        # Start two threads trying to update simultaneously
        thread1 = Thread(target=update_document, args=(1,))
        thread2 = Thread(target=update_document, args=(2,))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # One should succeed, one should fail with version conflict
        assert len(results) == 1, "Exactly one update should succeed"
        assert len(errors) == 1, "Exactly one update should fail"
        assert "modified by another user" in errors[0][1].lower()
        # The successful update should have incremented version
        assert results[0][1] == initial_version + 1


@pytest.mark.django_db
class TestCaseDocumentSoftDelete:
    """Tests for soft delete in CaseDocument."""

    def test_soft_delete_case_document(self, case_document):
        """Soft deleting a document should mark it as deleted."""
        initial_version = case_document.version
        
        deleted = CaseDocumentRepository.soft_delete_case_document(
            case_document,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, case_document):
        """Soft-deleted documents should not appear in selectors."""
        # Document should be visible before deletion
        found = CaseDocumentSelector.get_by_id(str(case_document.id))
        assert found is not None
        
        # Soft delete
        CaseDocumentRepository.soft_delete_case_document(
            case_document,
            version=case_document.version
        )
        
        # Document should not be visible after deletion
        with pytest.raises(CaseDocument.DoesNotExist):
            CaseDocumentSelector.get_by_id(str(case_document.id))

    def test_soft_delete_version_conflict_raises_error(self, case_document):
        """Soft deleting with wrong version should raise ValidationError."""
        initial_version = case_document.version
        
        # First update changes version
        CaseDocumentRepository.update_case_document(
            case_document,
            version=initial_version,
            file_name="updated.pdf"
        )
        
        # Soft delete with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            CaseDocumentRepository.soft_delete_case_document(
                case_document,
                version=initial_version  # Stale version
            )
        
        assert "modified by another user" in str(exc_info.value).lower()

    def test_restore_case_document(self, case_document):
        """Restoring a soft-deleted document should make it visible again."""
        initial_version = case_document.version
        
        # Soft delete
        deleted = CaseDocumentRepository.soft_delete_case_document(
            case_document,
            version=initial_version
        )
        assert deleted.is_deleted is True
        
        # Restore
        restored = CaseDocumentRepository.restore_case_document(
            deleted,
            version=deleted.version
        )
        
        assert restored.is_deleted is False
        assert restored.deleted_at is None
        assert restored.version == deleted.version + 1
        
        # Should be visible in selector again
        found = CaseDocumentSelector.get_by_id(str(restored.id))
        assert found is not None

    def test_service_delete_uses_soft_delete(self, case_document_service, case_document):
        """Service delete method should use soft delete."""
        initial_version = case_document.version
        
        result = case_document_service.delete_case_document(
            str(case_document.id),
            version=initial_version
        )
        
        assert result is True
        
        # Document should be soft-deleted
        from document_handling.models.case_document import CaseDocument
        deleted_doc = CaseDocument.objects.get(id=case_document.id)
        assert deleted_doc.is_deleted is True
        
        # Should not appear in selector
        with pytest.raises(CaseDocument.DoesNotExist):
            CaseDocumentSelector.get_by_id(str(case_document.id))


@pytest.mark.django_db
class TestDocumentCheckOptimisticLocking:
    """Tests for optimistic locking in DocumentCheck."""

    def test_create_document_check_has_version_one(self, document_check):
        """New checks should start with version 1."""
        assert document_check.version == 1
        assert document_check.is_deleted is False
        assert document_check.deleted_at is None

    def test_update_document_check_increments_version(self, document_check):
        """Updating a check should increment its version."""
        initial_version = document_check.version
        
        updated = DocumentCheckRepository.update_document_check(
            document_check,
            version=initial_version,
            result="failed"
        )
        
        assert updated.version == initial_version + 1
        assert updated.result == "failed"

    def test_update_document_check_version_conflict_raises_error(self, document_check):
        """Updating with wrong version should raise ValidationError."""
        initial_version = document_check.version
        
        # First update succeeds
        DocumentCheckRepository.update_document_check(
            document_check,
            version=initial_version,
            result="failed"
        )
        
        # Second update with stale version should fail
        with pytest.raises(ValidationError) as exc_info:
            DocumentCheckRepository.update_document_check(
                document_check,
                version=initial_version,  # Stale version
                result="passed"
            )
        
        assert "modified by another user" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestDocumentCheckSoftDelete:
    """Tests for soft delete in DocumentCheck."""

    def test_soft_delete_document_check(self, document_check):
        """Soft deleting a check should mark it as deleted."""
        initial_version = document_check.version
        
        deleted = DocumentCheckRepository.soft_delete_document_check(
            document_check,
            version=initial_version
        )
        
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None
        assert deleted.version == initial_version + 1

    def test_soft_delete_filters_from_selector(self, document_check):
        """Soft-deleted checks should not appear in selectors."""
        # Check should be visible before deletion
        found = DocumentCheckSelector.get_by_id(str(document_check.id))
        assert found is not None
        
        # Soft delete
        DocumentCheckRepository.soft_delete_document_check(
            document_check,
            version=document_check.version
        )
        
        # Check should not be visible after deletion
        with pytest.raises(DocumentCheck.DoesNotExist):
            DocumentCheckSelector.get_by_id(str(document_check.id))

    def test_service_delete_uses_soft_delete(self, document_check_service, document_check):
        """Service delete method should use soft delete."""
        initial_version = document_check.version
        
        result = document_check_service.delete_document_check(
            str(document_check.id),
            version=initial_version
        )
        
        assert result is True
        
        # Check should be soft-deleted
        from document_handling.models.document_check import DocumentCheck
        deleted_check = DocumentCheck.objects.get(id=document_check.id)
        assert deleted_check.is_deleted is True
        
        # Should not appear in selector
        with pytest.raises(DocumentCheck.DoesNotExist):
            DocumentCheckSelector.get_by_id(str(document_check.id))

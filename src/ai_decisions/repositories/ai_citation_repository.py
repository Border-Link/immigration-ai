from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from ai_decisions.models.ai_citation import AICitation
from ai_decisions.models.ai_reasoning_log import AIReasoningLog
from data_ingestion.models.document_version import DocumentVersion


class AICitationRepository:
    """Repository for AICitation write operations."""

    @staticmethod
    def create_citation(reasoning_log: AIReasoningLog, document_version: DocumentVersion,
                       excerpt: str, relevance_score: float = None):
        """Create a new AI citation."""
        with transaction.atomic():
            citation = AICitation.objects.create(
                reasoning_log=reasoning_log,
                document_version=document_version,
                excerpt=excerpt,
                relevance_score=relevance_score,
                version=1,
                is_deleted=False,
            )
            citation.full_clean()
            citation.save()
            return citation

    @staticmethod
    def update_citation(citation: AICitation, version: int = None, **fields):
        """Update citation fields with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(citation, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed = {"excerpt", "relevance_score"}
            update_fields = {k: v for k, v in fields.items() if k in allowed}
            update_fields["updated_at"] = timezone.now()

            updated = AICitation.objects.filter(
                id=citation.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = AICitation.objects.filter(id=citation.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("AI citation not found.")
                raise ValidationError(
                    f"AI citation was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AICitation.objects.get(id=citation.id)

    @staticmethod
    def soft_delete_citation(citation: AICitation, version: int = None) -> AICitation:
        """Soft delete an AI citation with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(citation, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            updated = AICitation.objects.filter(
                id=citation.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=timezone.now(),
                updated_at=timezone.now(),
                version=F("version") + 1,
            )

            if updated != 1:
                current_version = AICitation.objects.filter(id=citation.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("AI citation not found.")
                raise ValidationError(
                    f"AI citation was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return AICitation.objects.get(id=citation.id)

    @staticmethod
    def delete_citation(citation: AICitation, version: int = None):
        """
        Delete an AI citation.

        CRITICAL: deletion must be soft-delete.
        """
        return AICitationRepository.soft_delete_citation(citation, version=version)


import uuid
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.conf import settings
from .visa_type import VisaType


class VisaRuleVersion(models.Model):
    """
    Temporal versioning of immigration rules.
    Each version has an effective date range and links to the source document version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    visa_type = models.ForeignKey(
        VisaType,
        on_delete=models.CASCADE,
        related_name='rule_versions',
        db_index=True,
        help_text="The visa type this rule version applies to"
    )
    
    effective_from = models.DateTimeField(
        db_index=True,
        help_text="When this rule version becomes effective"
    )
    
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this rule version expires (NULL means current)"
    )
    
    source_document_version = models.ForeignKey(
        'data_ingestion.DocumentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rule_versions',
        db_index=True,
        help_text="The document version this rule was extracted from"
    )
    
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this rule version is published and available for use"
    )
    
    # Soft delete fields
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this rule version is soft deleted"
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this rule version was deleted"
    )
    
    # Audit trail fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rule_versions',
        help_text="User who created this rule version"
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_rule_versions',
        help_text="User who last updated this rule version"
    )
    
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_rule_versions',
        help_text="User who published this rule version"
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this rule version was published"
    )
    
    # Optimistic locking field
    version = models.IntegerField(
        default=1,
        help_text="Version number for optimistic locking to prevent concurrent modification conflicts"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visa_rule_versions'
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['visa_type', 'effective_from', 'effective_to']),
            models.Index(fields=['is_published', 'effective_from']),
            models.Index(fields=['is_deleted', 'is_published']),
            models.Index(fields=['visa_type', 'is_published', 'effective_from', 'effective_to']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(effective_to__isnull=True) | Q(effective_to__gte=F('effective_from')),
                name='effective_to_after_effective_from'
            ),
        ]
        verbose_name_plural = 'Visa Rule Versions'

    def __str__(self):
        return f"{self.visa_type.name} - Version {self.effective_from.date()}"

    def is_current(self):
        """Check if this rule version is currently effective."""
        if self.is_deleted:
            return False
        now = timezone.now()
        if self.effective_to:
            return self.effective_from <= now <= self.effective_to
        return self.effective_from <= now


import uuid
from django.db import models
from django.conf import settings
from .document_version import DocumentVersion


class ParsedRule(models.Model):
    """
    AI-extracted rule candidates from document versions (staging area).
    These rules require human validation before being promoted to production.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]

    RULE_TYPE_CHOICES = [
        ('eligibility', 'Eligibility Requirement'),
        ('document', 'Document Requirement'),
        ('fee', 'Fee Information'),
        ('processing_time', 'Processing Time'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='parsed_rules',
        db_index=True,
        help_text="The document version this rule was extracted from"
    )
    
    visa_code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Visa type code (e.g., 'SKILLED_WORKER', 'STUDENT')"
    )
    
    rule_type = models.CharField(
        max_length=50,
        choices=RULE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of rule extracted"
    )
    
    extracted_logic = models.JSONField(
        help_text="JSON Logic expression representing the rule condition"
    )
    
    description = models.TextField(
        help_text="Human-readable description of the requirement"
    )
    
    source_excerpt = models.TextField(
        help_text="Original text excerpt from the document"
    )
    
    confidence_score = models.FloatField(
        default=0.0,
        db_index=True,
        help_text="Confidence score (0.0 to 1.0) for the extraction quality"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Validation status of the parsed rule"
    )
    
    # LLM metadata tracking
    llm_model = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="LLM model used for extraction (e.g., 'gpt-4-turbo-preview')"
    )
    
    llm_model_version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Version of the LLM model used"
    )
    
    # Cost tracking
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens used for this extraction"
    )
    
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Estimated cost in USD for this extraction"
    )
    
    # Processing metadata
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing time in milliseconds"
    )
    
    error_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="Type of error if parsing failed (e.g., 'rate_limit', 'timeout')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parsed_rules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_version', 'status']),
            models.Index(fields=['visa_code', 'status']),
            models.Index(fields=['status', '-confidence_score']),
        ]
        verbose_name_plural = 'Parsed Rules'

    def __str__(self):
        return f"{self.visa_code} - {self.rule_type} ({self.status})"


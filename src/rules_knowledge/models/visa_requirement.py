import uuid
from django.db import models
from .visa_rule_version import VisaRuleVersion


class VisaRequirement(models.Model):
    """
    Atomic eligibility requirements with machine-readable logic.
    Each requirement is linked to a rule version and contains JSON Logic expressions.
    """
    RULE_TYPE_CHOICES = [
        ('eligibility', 'Eligibility Requirement'),
        ('document', 'Document Requirement'),
        ('fee', 'Fee Information'),
        ('processing_time', 'Processing Time'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    rule_version = models.ForeignKey(
        VisaRuleVersion,
        on_delete=models.CASCADE,
        related_name='requirements',
        db_index=True,
        help_text="The rule version this requirement belongs to"
    )
    
    requirement_code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique code for the requirement (e.g., 'MIN_SALARY', 'AGE_LIMIT')"
    )
    
    rule_type = models.CharField(
        max_length=50,
        choices=RULE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of requirement"
    )
    
    description = models.TextField(
        help_text="Human-readable description of the requirement"
    )
    
    condition_expression = models.JSONField(
        help_text="JSON Logic expression representing the requirement condition"
    )
    
    is_mandatory = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this requirement is mandatory"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visa_requirements'
        ordering = ['requirement_code']
        unique_together = [['rule_version', 'requirement_code']]
        indexes = [
            models.Index(fields=['rule_version', 'is_mandatory']),
            models.Index(fields=['rule_type', 'is_mandatory']),
            models.Index(fields=['rule_version', 'requirement_code']),
        ]
        verbose_name_plural = 'Visa Requirements'

    def __str__(self):
        return f"{self.requirement_code} - {self.rule_version.visa_type.name}"


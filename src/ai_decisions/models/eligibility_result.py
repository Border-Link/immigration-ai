import uuid
from django.db import models
from immigration_cases.models.case import Case
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.models.visa_rule_version import VisaRuleVersion


class EligibilityResult(models.Model):
    """
    Final eligibility outcome per visa route.
    Result of rule engine + AI reasoning evaluation.
    """
    OUTCOME_CHOICES = [
        ('eligible', 'Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('requires_review', 'Requires Review'),
        ('missing_facts', 'Missing Facts'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='eligibility_results',
        db_index=True,
        help_text="The case this result belongs to"
    )
    
    visa_type = models.ForeignKey(
        VisaType,
        on_delete=models.CASCADE,
        related_name='eligibility_results',
        db_index=True,
        help_text="The visa type evaluated"
    )
    
    rule_version = models.ForeignKey(
        VisaRuleVersion,
        on_delete=models.CASCADE,
        related_name='eligibility_results',
        db_index=True,
        help_text="The rule version used for evaluation"
    )
    
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        db_index=True,
        help_text="Final eligibility outcome"
    )
    
    confidence = models.FloatField(
        default=0.0,
        help_text="Confidence score (0.0 to 1.0) for the outcome"
    )
    
    reasoning_summary = models.TextField(
        null=True,
        blank=True,
        help_text="Summary of the reasoning for this outcome"
    )
    
    missing_facts = models.JSONField(
        null=True,
        blank=True,
        help_text="List of missing facts if outcome is 'missing_facts'"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'eligibility_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'visa_type']),
            models.Index(fields=['outcome', '-created_at']),
        ]
        verbose_name_plural = 'Eligibility Results'

    def __str__(self):
        return f"{self.case.id} - {self.visa_type.name}: {self.outcome}"


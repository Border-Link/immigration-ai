import uuid
from django.db import models
from django.conf import settings
from immigration_cases.models.case import Case
from ai_decisions.models.eligibility_result import EligibilityResult


class DecisionOverride(models.Model):
    """
    Human authority over AI decisions.
    Allows reviewers to override AI eligibility results.
    """
    OUTCOME_CHOICES = [
        ('eligible', 'Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('requires_review', 'Requires Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='decision_overrides',
        db_index=True,
        help_text="The case this override applies to"
    )
    
    original_result = models.ForeignKey(
        EligibilityResult,
        on_delete=models.CASCADE,
        related_name='overrides',
        db_index=True,
        help_text="The original AI eligibility result being overridden"
    )
    
    overridden_outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        db_index=True,
        help_text="The new outcome after override"
    )
    
    reason = models.TextField(
        help_text="Reason for the override"
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decision_overrides',
        db_index=True,
        help_text="The reviewer who made the override"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'decision_overrides'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', '-created_at']),
            models.Index(fields=['original_result', '-created_at']),
        ]
        verbose_name_plural = 'Decision Overrides'

    def __str__(self):
        return f"Override for Case {self.case.id} - {self.overridden_outcome}"


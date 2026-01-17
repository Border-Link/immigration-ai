import uuid
from django.db import models
from immigration_cases.models.case import Case


class AIReasoningLog(models.Model):
    """
    Full AI reasoning trace for explainability.
    Stores prompts, responses, and model information.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='ai_reasoning_logs',
        db_index=True,
        help_text="The case this reasoning log belongs to"
    )
    
    prompt = models.TextField(
        help_text="The prompt sent to the LLM"
    )
    
    response = models.TextField(
        help_text="The response from the LLM"
    )
    
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the LLM model used (e.g., 'gpt-4', 'claude-3')"
    )
    
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens used in the API call"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_reasoning_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', '-created_at']),
        ]
        verbose_name_plural = 'AI Reasoning Logs'

    def __str__(self):
        return f"AI Reasoning for Case {self.case.id} ({self.model_name})"


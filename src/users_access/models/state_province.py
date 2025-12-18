import uuid
from django.db import models
from .country import Country


class StateProvince(models.Model):
    """
    State/Province model - For countries with states/provinces.
    Needed for programs like Canada PNP, Australia State Nomination.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='states_provinces',
        db_index=True
    )
    
    code = models.CharField(
        max_length=10,
        db_index=True,
        help_text="State/Province code (e.g., 'ON', 'NSW')"
    )
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Full name (e.g., 'Ontario', 'New South Wales')"
    )
    
    # Immigration Context
    has_nomination_program = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this state/province has an immigration nomination program"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'states_provinces'
        ordering = ['country', 'name']
        unique_together = [['country', 'code']]
        indexes = [
            models.Index(fields=['country', 'code']),
            models.Index(fields=['has_nomination_program']),
        ]
        verbose_name_plural = 'States/Provinces'
    
    def __str__(self):
        return f"{self.name}, {self.country.code}"


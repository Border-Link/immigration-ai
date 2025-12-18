import uuid
from django.db import models


class Country(models.Model):
    """
    Country model - Simple country list for nationality and jurisdiction.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    # Basic identification
    code = models.CharField(
        max_length=2,
        unique=True,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 code (e.g., 'NG', 'GB', 'US')"
    )
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Country name (e.g., 'Nigeria', 'United Kingdom')"
    )
    
    # Immigration Context
    has_states = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this country has states/provinces (e.g., Canada, Australia, US)"
    )
    is_jurisdiction = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this country is a supported immigration jurisdiction"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'countries'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_jurisdiction', 'is_active']),
        ]
        verbose_name_plural = 'Countries'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


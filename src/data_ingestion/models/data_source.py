import uuid
from django.db import models


class DataSource(models.Model):
    """
    Configuration for monitored data sources (gov.uk pages, PDFs, APIs).
    Each source represents a jurisdiction-specific immigration information source.
    """
    JURISDICTION_CHOICES = [
        ('UK', 'United Kingdom'),
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Human-readable name for the data source (e.g., 'UK Gov Immigration Pages')"
    )
    
    base_url = models.URLField(
        max_length=500,
        help_text="Base URL for the data source (e.g., 'https://www.gov.uk/api/content')"
    )
    
    jurisdiction = models.CharField(
        max_length=10,
        choices=JURISDICTION_CHOICES,
        db_index=True,
        help_text="Jurisdiction this source belongs to (UK, US, CA, AU)"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this source is currently being monitored"
    )
    
    crawl_frequency = models.CharField(
        max_length=50,
        default='daily',
        help_text="How often to check for updates (daily, weekly, hourly)"
    )
    
    last_fetched_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Last time this source was successfully fetched"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'data_sources'
        ordering = ['jurisdiction', 'name']
        indexes = [
            models.Index(fields=['jurisdiction', 'is_active']),
        ]
        verbose_name_plural = 'Data Sources'

    def __str__(self):
        return f"{self.name} ({self.jurisdiction})"


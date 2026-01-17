import uuid
from django.db import models
from django.utils.timezone import now


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    level = models.CharField(max_length=50, db_index=True)
    logger_name = models.CharField(max_length=255, db_index=True)
    message = models.TextField()
    timestamp = models.DateTimeField(default=now, db_index=True)
    pathname = models.TextField(null=True, blank=True)
    lineno = models.IntegerField(null=True, blank=True)
    func_name = models.CharField(max_length=255, null=True, blank=True)
    process = models.IntegerField(null=True, blank=True)
    thread = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optimistic locking
    version = models.IntegerField(default=1, db_index=True, help_text="Version number for optimistic locking")

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'audit_logs'

    def __str__(self):
        return f"[{self.level}] {self.logger_name} @ {self.timestamp}"


# Generated manually for optimistic locking and soft delete

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("document_processing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="processingjob",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="processingjob",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this job is soft-deleted"),
        ),
        migrations.AddField(
            model_name="processingjob",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this job was soft-deleted", null=True),
        ),
        migrations.AddField(
            model_name="processinghistory",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="processinghistory",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this history entry is soft-deleted"),
        ),
        migrations.AddField(
            model_name="processinghistory",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this history entry was soft-deleted", null=True),
        ),
    ]

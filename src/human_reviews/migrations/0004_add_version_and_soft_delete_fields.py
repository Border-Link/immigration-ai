# Generated manually for optimistic locking and soft delete

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("human_reviews", "0003_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this review is soft-deleted"),
        ),
        migrations.AddField(
            model_name="review",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this review was soft-deleted", null=True),
        ),
        migrations.AddField(
            model_name="reviewnote",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="reviewnote",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this note is soft-deleted"),
        ),
        migrations.AddField(
            model_name="reviewnote",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this note was soft-deleted", null=True),
        ),
        migrations.AddField(
            model_name="decisionoverride",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="decisionoverride",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this override is soft-deleted"),
        ),
        migrations.AddField(
            model_name="decisionoverride",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this override was soft-deleted", null=True),
        ),
        migrations.AddField(
            model_name="reviewstatushistory",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="reviewstatushistory",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this history entry is soft-deleted"),
        ),
        migrations.AddField(
            model_name="reviewstatushistory",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this history entry was soft-deleted", null=True),
        ),
    ]

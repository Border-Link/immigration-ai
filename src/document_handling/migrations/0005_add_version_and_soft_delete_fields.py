# Generated manually for optimistic locking and soft delete

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("document_handling", "0004_alter_casedocument_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="casedocument",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="casedocument",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this document is soft-deleted"),
        ),
        migrations.AddField(
            model_name="casedocument",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this document was soft-deleted", null=True),
        ),
        migrations.AddField(
            model_name="documentcheck",
            name="version",
            field=models.IntegerField(db_index=True, default=1, help_text="Version number for optimistic locking"),
        ),
        migrations.AddField(
            model_name="documentcheck",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, help_text="Whether this check is soft-deleted"),
        ),
        migrations.AddField(
            model_name="documentcheck",
            name="deleted_at",
            field=models.DateTimeField(blank=True, help_text="When this check was soft-deleted", null=True),
        ),
    ]

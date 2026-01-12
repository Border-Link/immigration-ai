# Generated migration for adding timebox_task_id field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_calls', '0002_add_retry_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='callsession',
            name='timebox_task_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Celery task ID for timebox enforcement (for cancellation)',
                max_length=255,
                null=True
            ),
        ),
    ]

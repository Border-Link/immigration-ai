# Generated migration for retry tracking fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_calls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='callsession',
            name='retry_count',
            field=models.IntegerField(default=0, help_text='Number of retry attempts for this call session (max 3 per case)'),
        ),
        migrations.AddField(
            model_name='callsession',
            name='parent_session',
            field=models.ForeignKey(
                blank=True,
                help_text='Parent session if this is a retry',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='retry_sessions',
                to='ai_calls.callsession'
            ),
        ),
    ]

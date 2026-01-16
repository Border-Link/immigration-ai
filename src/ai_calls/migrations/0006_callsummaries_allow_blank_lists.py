from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_calls", "0005_callsession_add_last_heartbeat_and_audit_system_error"),
    ]

    operations = [
        migrations.AlterField(
            model_name="callsummary",
            name="action_items",
            field=models.JSONField(blank=True, default=list, help_text="List of action items identified"),
        ),
        migrations.AlterField(
            model_name="callsummary",
            name="key_questions",
            field=models.JSONField(blank=True, default=list, help_text="List of key questions asked during the call"),
        ),
        migrations.AlterField(
            model_name="callsummary",
            name="missing_documents",
            field=models.JSONField(blank=True, default=list, help_text="List of missing documents identified"),
        ),
        migrations.AlterField(
            model_name="callsummary",
            name="suggested_next_steps",
            field=models.JSONField(blank=True, default=list, help_text="List of suggested next steps (non-binding)"),
        ),
        migrations.AlterField(
            model_name="callsummary",
            name="topics_discussed",
            field=models.JSONField(blank=True, default=list, help_text="List of topics discussed"),
        ),
    ]


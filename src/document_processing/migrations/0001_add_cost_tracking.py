# Generated migration for cost tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document_processing', '0000_initial'),  # This will be created if models already exist
    ]

    operations = [
        # Add cost tracking fields to ProcessingJob
        migrations.AddField(
            model_name='processingjob',
            name='llm_tokens_used',
            field=models.IntegerField(blank=True, null=True, help_text='Number of LLM tokens used'),
        ),
        migrations.AddField(
            model_name='processingjob',
            name='llm_cost_usd',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True, help_text='LLM cost in USD'),
        ),
        migrations.AddField(
            model_name='processingjob',
            name='ocr_cost_usd',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True, help_text='OCR cost in USD'),
        ),
        migrations.AddField(
            model_name='processingjob',
            name='total_cost_usd',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=10, null=True, help_text='Total processing cost in USD'),
        ),
    ]

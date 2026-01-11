# Generated migration for human_reviews models

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('immigration_cases', '0001_initial'),  # Assuming immigration_cases has initial migration
        ('ai_decisions', '0001_initial'),  # Assuming ai_decisions has initial migration
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='pending', help_text='Current status of the review', max_length=20)),
                ('assigned_at', models.DateTimeField(blank=True, db_index=True, help_text='When the review was assigned', null=True)),
                ('completed_at', models.DateTimeField(blank=True, db_index=True, help_text='When the review was completed', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case', models.ForeignKey(db_index=True, help_text='The case being reviewed', on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='immigration_cases.case')),
                ('reviewer', models.ForeignKey(blank=True, db_index=True, help_text='The reviewer assigned to this review', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'reviews',
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Reviews',
            },
        ),
        migrations.CreateModel(
            name='ReviewNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ('note', models.TextField(help_text='The note content')),
                ('is_internal', models.BooleanField(db_index=True, default=False, help_text='Whether this note is internal (not visible to user)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('review', models.ForeignKey(db_index=True, help_text='The review this note belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='human_reviews.review')),
            ],
            options={
                'db_table': 'review_notes',
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Review Notes',
            },
        ),
        migrations.CreateModel(
            name='DecisionOverride',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ('overridden_outcome', models.CharField(choices=[('eligible', 'Eligible'), ('not_eligible', 'Not Eligible'), ('requires_review', 'Requires Review')], db_index=True, help_text='The new outcome after override', max_length=20)),
                ('reason', models.TextField(help_text='Reason for the override')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('case', models.ForeignKey(db_index=True, help_text='The case this override applies to', on_delete=django.db.models.deletion.CASCADE, related_name='decision_overrides', to='immigration_cases.case')),
                ('original_result', models.ForeignKey(db_index=True, help_text='The original AI eligibility result being overridden', on_delete=django.db.models.deletion.CASCADE, related_name='overrides', to='ai_decisions.eligibilityresult')),
                ('reviewer', models.ForeignKey(blank=True, db_index=True, help_text='The reviewer who made the override', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='decision_overrides', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'decision_overrides',
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Decision Overrides',
            },
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['case', 'status'], name='reviews_case_status_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['reviewer', 'status'], name='reviews_reviewer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='decisionoverride',
            index=models.Index(fields=['case', '-created_at'], name='decision_over_case_created_idx'),
        ),
        migrations.AddIndex(
            model_name='decisionoverride',
            index=models.Index(fields=['original_result', '-created_at'], name='decision_over_result_created_idx'),
        ),
    ]

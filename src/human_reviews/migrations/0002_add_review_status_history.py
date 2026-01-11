# Generated migration for ReviewStatusHistory model

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('human_reviews', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewStatusHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ('previous_status', models.CharField(blank=True, help_text='Previous status before change', max_length=20, null=True)),
                ('new_status', models.CharField(help_text='New status after change', max_length=20)),
                ('reason', models.TextField(blank=True, help_text='Reason for the status change', null=True)),
                ('metadata', models.JSONField(blank=True, help_text='Additional metadata about the status change', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('changed_by', models.ForeignKey(blank=True, help_text='User who made the status change', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_status_changes', to=settings.AUTH_USER_MODEL)),
                ('review', models.ForeignKey(db_index=True, help_text='The review this status change belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='human_reviews.review')),
            ],
            options={
                'db_table': 'review_status_history',
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Review Status History',
            },
        ),
        migrations.AddIndex(
            model_name='reviewstatushistory',
            index=models.Index(fields=['review', '-created_at'], name='review_stat_review_created_idx'),
        ),
        migrations.AddIndex(
            model_name='reviewstatushistory',
            index=models.Index(fields=['changed_by', '-created_at'], name='review_stat_changed_created_idx'),
        ),
        migrations.AddIndex(
            model_name='reviewstatushistory',
            index=models.Index(fields=['new_status', '-created_at'], name='review_stat_status_created_idx'),
        ),
    ]

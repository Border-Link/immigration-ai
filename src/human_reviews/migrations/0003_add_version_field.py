# Generated migration to add version field for optimistic locking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('human_reviews', '0002_add_review_status_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='version',
            field=models.IntegerField(db_index=True, default=1, help_text='Version number for optimistic locking'),
        ),
    ]

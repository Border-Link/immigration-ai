# Generated migration to add version field for optimistic locking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='version',
            field=models.IntegerField(db_index=True, default=1, help_text='Version number for optimistic locking'),
        ),
    ]

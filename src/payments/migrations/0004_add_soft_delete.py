# Generated migration to add soft delete fields to payment model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_add_database_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, help_text='Whether this payment is soft deleted'),
        ),
        migrations.AddField(
            model_name='payment',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='When this payment was deleted', null=True),
        ),
    ]

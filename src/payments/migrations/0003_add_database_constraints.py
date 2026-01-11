# Generated migration to add database constraints for payment model

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_add_version_field'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                check=Q(status__in=['pending', 'processing', 'completed', 'failed', 'refunded']),
                name='valid_payment_status'
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                check=Q(amount__gt=0),
                name='positive_payment_amount'
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                check=Q(retry_count__gte=0),
                name='non_negative_retry_count'
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                check=Q(max_retries__gte=0),
                name='non_negative_max_retries'
            ),
        ),
    ]

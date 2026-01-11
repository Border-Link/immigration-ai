# Generated migration for optimistic locking version field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rules_knowledge', '0001_add_soft_delete_and_audit_trail'),
    ]

    operations = [
        # Add version field for optimistic locking to VisaRuleVersion
        migrations.AddField(
            model_name='visaruleversion',
            name='version',
            field=models.IntegerField(
                default=1,
                help_text='Version number for optimistic locking to prevent concurrent modification conflicts'
            ),
        ),
    ]

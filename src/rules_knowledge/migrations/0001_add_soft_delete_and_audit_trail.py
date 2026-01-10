# Generated migration for soft delete and audit trail fields

import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('rules_knowledge', '0000_initial'),  # This will be created if models already exist
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add soft delete fields to VisaRuleVersion
        migrations.AddField(
            model_name='visaruleversion',
            name='is_deleted',
            field=models.BooleanField(default=False, db_index=True, help_text='Whether this rule version is soft deleted'),
        ),
        migrations.AddField(
            model_name='visaruleversion',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, db_index=True, help_text='When this rule version was deleted'),
        ),
        # Add audit trail fields to VisaRuleVersion
        migrations.AddField(
            model_name='visaruleversion',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_rule_versions',
                to=settings.AUTH_USER_MODEL,
                help_text='User who created this rule version'
            ),
        ),
        migrations.AddField(
            model_name='visaruleversion',
            name='updated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='updated_rule_versions',
                to=settings.AUTH_USER_MODEL,
                help_text='User who last updated this rule version'
            ),
        ),
        migrations.AddField(
            model_name='visaruleversion',
            name='published_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='published_rule_versions',
                to=settings.AUTH_USER_MODEL,
                help_text='User who published this rule version'
            ),
        ),
        migrations.AddField(
            model_name='visaruleversion',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True, db_index=True, help_text='When this rule version was published'),
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='visaruleversion',
            index=models.Index(fields=['is_deleted', 'is_published'], name='visa_rule_v_is_dele_idx'),
        ),
        migrations.AddIndex(
            model_name='visaruleversion',
            index=models.Index(fields=['visa_type', 'is_published', 'effective_from', 'effective_to'], name='visa_rule_v_visa_ty_idx'),
        ),
        # Add constraint for effective_to >= effective_from
        migrations.AddConstraint(
            model_name='visaruleversion',
            constraint=models.CheckConstraint(
                check=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F('effective_from')),
                name='effective_to_after_effective_from'
            ),
        ),
        # Add unique constraint for VisaRequirement
        migrations.AlterUniqueTogether(
            name='visarequirement',
            unique_together={('rule_version', 'requirement_code')},
        ),
        # Add index for requirement_code lookup
        migrations.AddIndex(
            model_name='visarequirement',
            index=models.Index(fields=['rule_version', 'requirement_code'], name='visa_requir_rule_ve_idx'),
        ),
    ]

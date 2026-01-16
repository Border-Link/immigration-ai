from django.db import migrations, models
from django.db.models import Q


def backfill_case_fee_plan(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    # Backfill legacy rows so the DB constraint can be enforced safely.
    Payment.objects.filter(purpose="case_fee").filter(Q(plan__isnull=True) | Q(plan="")).update(plan="basic")


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0007_pricing_items"),
    ]

    operations = [
        migrations.RunPython(backfill_case_fee_plan, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                name="payments_case_fee_requires_plan",
                condition=~Q(purpose="case_fee") | (~Q(plan__isnull=True) & ~Q(plan="")),
            ),
        ),
    ]


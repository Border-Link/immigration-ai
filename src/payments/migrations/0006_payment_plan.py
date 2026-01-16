from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0005_payment_purpose"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="plan",
            field=models.CharField(
                blank=True,
                choices=[("basic", "Basic Plan"), ("special", "Special Plan"), ("big", "Big Plan")],
                db_index=True,
                help_text="Plan purchased with the case fee payment (basic/special/big). Only applicable when purpose=case_fee.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["case", "purpose", "plan", "status"], name="payments_case_purpose_plan_status_idx"),
        ),
    ]


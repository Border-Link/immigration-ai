from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0004_remove_payment_payments_user_status_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="purpose",
            field=models.CharField(
                choices=[("case_fee", "Case Fee"), ("reviewer_addon", "Reviewer Add-on")],
                db_index=True,
                default="case_fee",
                help_text="What this payment is for (case fee vs add-ons like reviewer)",
                max_length=50,
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["case", "purpose", "status"], name="payments_ca_purpose_status_idx"),
        ),
    ]


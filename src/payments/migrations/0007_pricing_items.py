from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0006_payment_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="PricingItem",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True, serialize=False)),
                ("kind", models.CharField(max_length=20, choices=[("plan", "Plan"), ("addon", "Add-on")], db_index=True)),
                ("code", models.CharField(max_length=50, unique=True, db_index=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True, db_index=True)),
                ("includes_ai_calls", models.BooleanField(default=False)),
                ("includes_human_review", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "pricing_items",
                "ordering": ["kind", "code"],
            },
        ),
        migrations.CreateModel(
            name="PricingItemPrice",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True, serialize=False)),
                ("currency", models.CharField(max_length=3, db_index=True)),
                ("amount", models.DecimalField(max_digits=10, decimal_places=2)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("pricing_item", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="prices", to="payments.pricingitem", db_index=True)),
            ],
            options={
                "db_table": "pricing_item_prices",
                "ordering": ["pricing_item", "currency"],
            },
        ),
        migrations.AddConstraint(
            model_name="pricingitemprice",
            constraint=models.UniqueConstraint(fields=("pricing_item", "currency"), name="uniq_pricing_item_currency"),
        ),
        migrations.AddIndex(
            model_name="pricingitem",
            index=models.Index(fields=["kind", "is_active"], name="pricing_items_kind_active_idx"),
        ),
        migrations.AddIndex(
            model_name="pricingitemprice",
            index=models.Index(fields=["currency", "amount"], name="pricing_prices_currency_amount_idx"),
        ),
    ]


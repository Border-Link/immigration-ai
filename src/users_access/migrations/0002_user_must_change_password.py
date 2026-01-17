from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users_access", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="must_change_password",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bot", "0011_fix_task_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="full_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="platform_type",
            field=models.CharField(
                choices=[
                    ("telegram", "Telegram"),
                    ("whatsapp", "WhatsApp"),
                    ("api", "API"),
                ],
                default="telegram",
                max_length=20,
            ),
        ),
        migrations.RemoveField(
            model_name="user",
            name="link_code",
        ),
        migrations.RemoveField(
            model_name="user",
            name="link_code_expires",
        ),
        migrations.RemoveField(
            model_name="user",
            name="tenant_user",
        ),
        migrations.DeleteModel(
            name="TenantUser",
        ),
        migrations.DeleteModel(
            name="Tenant",
        ),
    ]

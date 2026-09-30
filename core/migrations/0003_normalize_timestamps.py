from django.db import migrations, models
from django.utils import timezone


def fill_missing_timestamps(apps, schema_editor):
    now = timezone.now()
    targets = {
        "SiteSettings": ["created_at"],
        "Profile": ["created_at", "updated_at"],
        "Skill": ["created_at", "updated_at"],
        "Project": ["updated_at"],
        "Certificate": ["created_at", "updated_at"],
        "Experience": ["created_at", "updated_at"],
        "Page": ["created_at", "updated_at"],
        "LegalPage": ["created_at"],
        "ContactMessage": ["updated_at"],
        "Appointment": ["updated_at"],
        "AutomationRule": ["created_at", "updated_at"],
    }
    for model_name, fields in targets.items():
        model = apps.get_model("core", model_name)
        for field in fields:
            model.objects.filter(**{f"{field}__isnull": True}).update(**{field: now})


class Migration(migrations.Migration):
    dependencies = [("core", "0002_platform")]

    operations = [
        migrations.RunPython(fill_missing_timestamps, migrations.RunPython.noop),
        migrations.AlterField("SiteSettings", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Profile", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Profile", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Skill", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Skill", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Project", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Certificate", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Certificate", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Experience", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Experience", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Page", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("Page", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("LegalPage", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("ContactMessage", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("Appointment", "updated_at", models.DateTimeField(auto_now=True)),
        migrations.AlterField("AutomationRule", "created_at", models.DateTimeField(auto_now_add=True)),
        migrations.AlterField("AutomationRule", "updated_at", models.DateTimeField(auto_now=True)),
    ]

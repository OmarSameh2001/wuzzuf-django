# Generated by Django 5.1.7 on 2025-04-29 18:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0009_application_created_at_application_updated_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="application",
            name="created_at",
        ),
        migrations.RemoveField(
            model_name="application",
            name="updated_at",
        ),
    ]

# Generated by Django 5.1.7 on 2025-05-04 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0026_merge_20250502_1359"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[],
        ),
        migrations.AddField(
            model_name="user",
            name="summary",
            field=models.TextField(blank=True, null=True),
        ),
    ]

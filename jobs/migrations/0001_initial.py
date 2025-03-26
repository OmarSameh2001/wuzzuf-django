# Generated by Django 5.1.7 on 2025-03-17 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Jobs",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("location", models.CharField(max_length=100)),
                ("keywords", models.CharField(max_length=255)),
                ("experince", models.CharField(max_length=100)),
                ("status", models.CharField(max_length=100)),
                ("type_of_job", models.CharField(max_length=100)),
            ],
        ),
    ]

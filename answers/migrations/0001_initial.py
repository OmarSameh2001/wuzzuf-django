# Generated by Django 5.1.7 on 2025-03-29 03:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("applications", "0001_initial"),
        ("questions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("answer_text", models.TextField()),
                ("result", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="applications.application",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="questions.question",
                    ),
                ),
            ],
        ),
    ]

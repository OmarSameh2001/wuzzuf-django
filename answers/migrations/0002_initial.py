# Generated by Django 5.1.8 on 2025-04-02 11:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("answers", "0001_initial"),
        ("applications", "0001_initial"),
        ("questions", "__first__"),
    ]

    operations = [
        migrations.AddField(
            model_name="answer",
            name="application",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="applications.application",
            ),
        ),
        migrations.AddField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="questions.question"
            ),
        ),
    ]

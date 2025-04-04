# Generated by Django 5.1.7 on 2025-04-04 14:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0006_job_company"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="company",
            field=models.ForeignKey(
                default=3,
                limit_choices_to={"user_type": "COMPANY"},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]

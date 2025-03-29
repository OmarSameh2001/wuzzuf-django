# Generated by Django 5.1.7 on 2025-03-26 18:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("status", models.CharField(default="1", max_length=50)),
                ("ats_res", models.TextField(blank=True, null=True)),
                ("screening_res", models.TextField(blank=True, null=True)),
                (
                    "assessment_link",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("assessment_res", models.TextField(blank=True, null=True)),
                (
                    "interview_link",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("interview_time", models.DateTimeField(blank=True, null=True)),
                ("interview_options_time", models.JSONField(blank=True, null=True)),
                ("hr_link", models.CharField(blank=True, max_length=255, null=True)),
                ("hr_time", models.DateTimeField(blank=True, null=True)),
                ("hr_time_options", models.JSONField(blank=True, null=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="jobs.job"
                    ),
                ),
            ],
        ),
    ]

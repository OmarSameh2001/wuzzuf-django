# Generated by Django 5.1.7 on 2025-03-30 10:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_alter_job_company"),
        ("user", "0003_delete_company_alter_user_managers_company"),
    ]

    operations = [
        migrations.AlterField(
            model_name="Job",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to="user.company",
            ),
        ),
    ]

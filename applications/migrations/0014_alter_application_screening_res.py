# Generated by Django 5.1.7 on 2025-05-11 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0013_application_insurance_application_termination_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="screening_res",
            field=models.FloatField(blank=True, null=True),
        ),
    ]

# Generated by Django 5.1.7 on 2025-04-01 17:12

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0005_alter_user_cv_alter_user_img"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="national_id_img",
            field=cloudinary.models.CloudinaryField(
                blank=True, max_length=255, null=True, verbose_name="image"
            ),
        ),
    ]

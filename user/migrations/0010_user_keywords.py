# Generated by Django 5.1.8 on 2025-04-04 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0009_merge_0008_alter_user_id_0008_user_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="keywords",
            field=models.TextField(blank=True, null=True),
        ),
    ]

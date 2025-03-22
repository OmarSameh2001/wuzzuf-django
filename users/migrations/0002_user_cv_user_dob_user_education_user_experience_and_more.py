# Generated by Django 5.1.7 on 2025-03-17 11:55

import django.core.validators
import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cv',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='dob',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='education',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='experience',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='img',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='keywords',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='national_id',
            field=models.CharField(blank=True, max_length=14, null=True, unique=True, validators=[users.models.validate_egyptian_national_id]),
        ),
        migrations.AddField(
            model_name='user',
            name='national_id_img',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=11, null=True, validators=[django.core.validators.RegexValidator(code='invalid_phone_number', message='Phone number must be a valid Egyptian number (e.g., 01012345678)', regex='^(01[0-2,5]{1}[0-9]{8})$')]),
        ),
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(default='default_user', max_length=50, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_username', message='Username must contain only letters, numbers, and underscores', regex='^[a-zA-Z0-9_]+$')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=255, unique=True, validators=[django.core.validators.EmailValidator(message='Enter a valid email address')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(code='invalid_name', message='Name must contain only letters and at least 3 characters', regex='^[a-zA-Z ]{3,}$')]),
        ),
    ]

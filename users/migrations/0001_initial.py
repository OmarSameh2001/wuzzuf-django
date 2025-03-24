# Generated by Django 5.1.7 on 2025-03-23 11:08

import cloudinary.models
import django.core.validators
import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=255,
                        unique=True,
                        validators=[
                            django.core.validators.EmailValidator(
                                message="Enter a valid email address"
                            )
                        ],
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        max_length=50,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_username",
                                message="Username must contain only letters, numbers, and underscores",
                                regex="^[a-zA-Z0-9_]+$",
                            )
                        ],
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_name",
                                message="Name must contain only letters and at least 3 characters",
                                regex="^[a-zA-Z ]{3,}$",
                            )
                        ],
                    ),
                ),
                ("dob", models.DateField(blank=True, null=True)),
                ("education", models.TextField(blank=True, null=True)),
                ("experience", models.TextField(blank=True, null=True)),
                (
                    "cv",
                    cloudinary.models.CloudinaryField(
                        blank=True, max_length=255, null=True, verbose_name="cv"
                    ),
                ),
                (
                    "img",
                    cloudinary.models.CloudinaryField(
                        blank=True, max_length=255, null=True, verbose_name="image"
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=255, null=True)),
                ("keywords", models.TextField(blank=True, null=True)),
                (
                    "national_id",
                    models.CharField(
                        blank=True,
                        max_length=14,
                        null=True,
                        unique=True,
                        validators=[users.models.validate_egyptian_national_id],
                    ),
                ),
                ("national_id_img", models.TextField(blank=True, null=True)),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        max_length=11,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_phone_number",
                                message="Phone number must be a valid Egyptian number (e.g., 01012345678)",
                                regex="^(01[0-2,5]{1}[0-9]{8})$",
                            )
                        ],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_company", models.BooleanField(default=False)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]

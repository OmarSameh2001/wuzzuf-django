from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
import re
import datetime

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("email field must be set")
        
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        if "name" not in extra_fields:
            raise ValueError("Superusers must have a name.")
        
        return self.create_user(email, password, **extra_fields)


# Custom Validator for Egyptian National ID
def validate_egyptian_national_id(value):
    if not value.isdigit() or len(value) != 14:
        raise ValidationError("National ID must be exactly 14 digits.")

    # Extracting Components
    century_code = value[0]
    year = int(value[1:3])  # YY
    month = int(value[3:5])  # MM
    day = int(value[5:7])  # DD
    governorate_code = int(value[7:9])  # Governorate

    # Determine full year
    if century_code == "2":
        year += 1900
    elif century_code == "3":
        year += 2000
    else:
        raise ValidationError("Invalid century digit in National ID.")

    # Validate date of birth
    try:
        dob = datetime.date(year, month, day)
        if dob > datetime.date.today():
            raise ValidationError("Birthdate in National ID cannot be in the future.")
    except ValueError:
        raise ValidationError("Invalid date of birth in National ID.")

    # Validate governorate code (01-35)
    if governorate_code < 1 or governorate_code > 35:
        raise ValidationError("Invalid governorate code in National ID.")

    return value



class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, validators=[EmailValidator(message="Enter a valid email address")])
    username = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        blank=False,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9_]+$',
            message="Username must contain only letters, numbers, and underscores",
            code='invalid_username'
        )]
    )
    name = models.CharField(max_length=255, validators=[RegexValidator(
            regex=r'^[a-zA-Z ]{3,}$',
            message="Name must contain only letters and at least 3 characters",
            code='invalid_name'
        )])
    dob = models.DateField(null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    cv = models.TextField(null=True, blank=True)
    img = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)  
    keywords = models.TextField(null=True, blank=True) 
    national_id = models.CharField(max_length=14, unique=True, null=True, blank=True,  validators=[validate_egyptian_national_id])
    national_id_img = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=11, null=True, blank=True, validators=[RegexValidator(
            regex=r'^(01[0-2,5]{1}[0-9]{8})$',
            message="Phone number must be a valid Egyptian number (e.g., 01012345678)",
            code='invalid_phone_number'
        )])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Required for Django admin
    is_company = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name'] # Required fields for createsuperuser


    def __str__(self):
        return self.email
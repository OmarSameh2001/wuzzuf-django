from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    Group, 
    Permission,
)
import re
import datetime

class CompanyManager(BaseUserManager):

    def create_company(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("email field must be set")
        
        email = self.normalize_email(email)

        company = self.model(email=email, **extra_fields)
        company.set_password(password)
        company.save(using=self._db)

        return company

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        if "name" not in extra_fields:
            raise ValueError("Superusers must have a name.")
        
        return self.create_company(email, password, **extra_fields)



# Custom Validator for Egyptian National ID
# def validate_egyptian_national_id(value):
#     if not value.isdigit() or len(value) != 14:
#         raise ValidationError("National ID must be exactly 14 digits.")

#     # Extracting Components
#     century_code = value[0]
#     year = int(value[1:3])  # YY
#     month = int(value[3:5])  # MM
#     day = int(value[5:7])  # DD
#     governorate_code = int(value[7:9])  # Governorate

#     # Determine full year
#     if century_code == "2":
#         year += 1900
#     elif century_code == "3":
#         year += 2000
#     else:
#         raise ValidationError("Invalid century digit in National ID.")

#     # Validate date of birth
#     try:
#         dob = datetime.date(year, month, day)
#         if dob > datetime.date.today():
#             raise ValidationError("Birthdate in National ID cannot be in the future.")
#     except ValueError:
#         raise ValidationError("Invalid date of birth in National ID.")

#     # Validate governorate code (01-35)
#     if governorate_code < 1 or governorate_code > 35:
#         raise ValidationError("Invalid governorate code in National ID.")

#     return value



class Company(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, validators=[EmailValidator(message="Enter a valid email address")])
    name = models.CharField(max_length=255, validators=[RegexValidator(
            regex=r'^[a-zA-Z ]{3,}$',
            message="Name must contain only letters and at least 3 characters",
            code='invalid_name'
        )])
    est = models.DateField(null=True, blank=True)
    img = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)  
    phone_number = models.CharField(max_length=11, null=True, blank=True, validators=[RegexValidator(
            regex=r'^(01[0-2,5]{1}[0-9]{8})$',
            message="Phone number must be a valid Egyptian number (e.g., 01012345678)",
            code='invalid_phone_number'
        )])
    industry = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # is_staff = models.BooleanField(default=False) # Required for Django admin
    is_company = models.BooleanField(default=True)

    groups = models.ManyToManyField(Group, related_name="company_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="company_permissions")

    objects = CompanyManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name'] # Required fields for createsuperuser


    def __str__(self):
        return self.email
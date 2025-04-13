from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
import datetime
from cloudinary.models import CloudinaryField


# Custom Validator for Egyptian National ID
def validate_egyptian_national_id(value):
    if not value.isdigit() or len(value) != 14:
        raise ValidationError("National ID must be exactly 14 digits.")

    century_code = value[0]
    year = int(value[1:3])
    month = int(value[3:5])
    day = int(value[5:7])
    governorate_code = int(value[7:9])

    if century_code == "2":
        year += 1900
    elif century_code == "3":
        year += 2000
    else:
        raise ValidationError("Invalid century digit in National ID.")

    try:
        dob = datetime.date(year, month, day)
        if dob > datetime.date.today():
            raise ValidationError("Birthdate in National ID cannot be in the future.")
    except ValueError:
        raise ValidationError("Invalid date of birth in National ID.")

    if governorate_code < 1 or governorate_code > 35:
        raise ValidationError("Invalid governorate code in National ID.")


class User(AbstractUser):
    class UserType(models.TextChoices):
        JOBSEEKER = "JOBSEEKER", "Jobseeker"
        COMPANY = "COMPANY", "Company"

    #shared fields
    id = models.AutoField(primary_key=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.JOBSEEKER
    )

    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address")],
    )
    name = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z ]{3,}$",
                message="Name must contain only letters and at least 3 characters",
            )
        ],
    )
    img = CloudinaryField('image', null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^(01[0-2,5]{1}[0-9]{8})$",
                message="Phone number must be a valid Egyptian number",
            )
        ],
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # OTP Verification Fields
    otp_digit = models.CharField(max_length=6, null=True, blank=True)  # Stores OTP code
    verify_status = models.BooleanField(default=False)  # False until verified
    is_active = models.BooleanField(default=False)  # False until verified

    #jobseeker fields
    about=models.TextField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    cv = CloudinaryField('cv', resource_type='raw', null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)
    national_id = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_egyptian_national_id],
    )
    national_id_img = CloudinaryField('image', null=True, blank=True)
    skills = models.TextField(null=True, blank=True)

    #company fields
    est = models.DateField(null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    logo = CloudinaryField('image', null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    def __str__(self):
        return self.email


class JobseekerManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type=User.UserType.JOBSEEKER)

class CompanyManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type=User.UserType.COMPANY)

class Jobseeker(User):
    objects = JobseekerManager()

    class Meta:
        proxy = True
        verbose_name = "Jobseeker"
        verbose_name_plural = "Jobseekers"

class Company(User):
    objects = CompanyManager()

    class Meta:
        proxy = True
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        
    def save(self, *args, **kwargs):
        """Ensure the user type is set to COMPANY when saving"""
        if not self.pk:  # Only set on new objects
            self.user_type = User.UserType.COMPANY
        super().save(*args, **kwargs)

class Itian(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        validators=[EmailValidator(message="Enter a valid email address")],
    )
    national_id = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_egyptian_national_id],
    )
    file = models.FileField(null=True, blank=True)
    # def __str__(self):
    #     return self.email
    

class JobseekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': User.UserType.JOBSEEKER})
    jobseeker_id = models.IntegerField(null=True, blank=True)

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': User.UserType.COMPANY})
    company_id = models.IntegerField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created and instance.is_active:
        Token.objects.create(user=instance)

@receiver(post_save, sender=Jobseeker)
def create_jobseeker_profile(sender, instance, created, **kwargs):
    if created:
        JobseekerProfile.objects.create(user=instance)


@receiver(post_save, sender=Company)
def create_company_profile(sender, instance, created, **kwargs):
    if created:
        CompanyProfile.objects.create(user=instance)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_type": user.user_type
        })


class JobseekerDashboard(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type == "JOBSEEKER":
            return Response({"message": "Welcome, Jobseeker!"})
        return Response({"error": "Unauthorized"}, status=403)

class CompanyDashboard(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type == "COMPANY":
            return Response({"message": "Welcome, Company!"})
        return Response({"error": "Unauthorized"}, status=403)
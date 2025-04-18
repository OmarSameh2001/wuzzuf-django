from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers
from .models import Company, Jobseeker, User, Itian
from cloudinary.uploader import upload
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'name', 'user_type', 'national_id', 'accounts']

        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}
    
    def create(self, validated_data):
        user_type = validated_data.pop("user_type", "jobseeker").upper()
        
        user = User(**validated_data)
        user.user_type = user_type

        if user_type == "ADMIN":
            user.is_staff = True
            user.is_superuser = True

        user.set_password(validated_data["password"])
        user.save()

        return user

    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class JobseekerProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    cv = serializers.CharField(allow_blank=True, required=False)
    img = serializers.CharField( allow_null=True ,required=False)
    national_id_img = serializers.CharField( allow_null=True ,required=False)
    
    #for file upload only to be write_only
    cv_file = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True
    ) 
     
     
    class Meta:
        model = Jobseeker 
        fields = [
            'id',
            'email', 
            'name',
            'about', 
            'dob', 
            'education', 
            'experience',
            'accounts', 
            'cv', 
            'img', 
            'national_id', 
            'national_id_img', 
            'location', 
            'phone_number',
            'skills',
            'user_type',
            'cv_file'
        ]
        read_only_fields = ['email']
    
    
    
    def update(self, instance, validated_data):
        # Handle CV file upload separately
        cv_file = validated_data.pop('cv_file', None)
        
        if cv_file is not None:
            if cv_file:  # New file uploaded
                cv_upload = upload(cv_file, resource_type="raw")
                validated_data['cv'] = cv_upload['secure_url']
            else:  # Explicit None means delete CV
                validated_data['cv'] = None
        
        # Handle image fields (can accept either file or URL)
        for image_field in ['img', 'national_id_img']:
            if image_field in validated_data:
                field_value = validated_data[image_field]
                if hasattr(field_value, 'file'):  # It's a file upload
                    image_upload = upload(field_value)
                    validated_data[image_field] = image_upload['secure_url']
                elif field_value == '':  # Empty string means clear the field
                    validated_data[image_field] = None

        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
class CompanyProfileSerializer(serializers.ModelSerializer):
    # logo=serializers.ImageField(required=False)
    class Meta:
        model = Company
        fields = [
            'id',
            'email', 
            'name',
            'est', 
            'industry', 
            'img',
            'location', 
            'phone_number',
            'user_type',
            'accounts',
            'is_verified'
            ]
        read_only_fields = ['email']
        
    def update(self, instance, validated_data):
            request = self.context.get('request')
        
            # Process file uploads if present in request.FILES
            if request and hasattr(request, "FILES"):
                if 'img' in request.FILES:
                    image_upload = upload(request.FILES['img'])
                    validated_data['img'] = image_upload['secure_url']

                if 'cv' in request.FILES:
                    cv_upload = upload(request.FILES['cv'], resource_type="raw")
                    validated_data['cv'] = cv_upload['secure_url']

                # if 'national_id_img' in request.FILES:
                #     national_id_upload = upload(request.FILES['national_id_img'])
                #     validated_data['national_id_img'] = national_id_upload['secure_url']
            
            # Now update the instance with the validated data
            # Ensure the instance fields are updated with validated data
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            # Save the updated instance to persist the changes
            instance.save()

            return instance


class ItianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Itian
        fields = '__all__'

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6) 


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """Ensure the email exists in the database"""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def send_password_reset_email(self):
        """Generate token and send reset email"""
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)

        # Generate a password reset link
        reset_url = f"http://localhost:5173/reset-password/{user.email}"

         # Email content
        email_body = (
            "You requested a password reset.\n\n"
            "Please visit the following page to reset your password:\n\n"
            f"{reset_url}\n\n"
        )


        # Send email
        send_mail(
            subject="Password Reset Request",
            message=email_body,
            from_email="hebagassem911@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """Check if email and token are valid before resetting password"""
        email = data.get("email")
        token = data.get("token")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        return data

    def save(self):
        """Update user password"""
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input-type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        print(f"Validating user: {email}, {password}, {user}")
        if not user:
            raise serializers.ValidationError(_('Unable to authenticate with provided credentials'), code='authorization')
        
        # Check if the user is a superuser (admin)
        if user.is_superuser:
            user.user_type = 'ADMIN'

        attrs['user'] = user
        return attrs
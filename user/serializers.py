from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers
from .models import Company, Jobseeker
from cloudinary.uploader import upload

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'name', 'user_type']

        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        user_type = validated_data.pop("user_type", "jobseeker")  # Default to jobseeker
        user = User.objects.create_user(**validated_data, user_type=user_type)
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class JobseekerProfileSerializer(serializers.ModelSerializer):
    cv = serializers.FileField(required=False)
    img = serializers.ImageField(required=False)
    national_id_img = serializers.ImageField(required=False)
    class Meta:
        model = Jobseeker
        fields = [
            'email', 
            'name', 
            'dob', 
            'education', 
            'experience', 
            'cv', 
            'img', 
            'national_id', 
            'national_id_img', 
            'location', 
            'phone_number',
            'skills'
            ]
        read_only_fields = ['email']

        def update(self, instance, validated_data):
            # Update the fields for the jobseeker model
          request = self.context.get('request')
          if request and hasattr(request, "FILES"):
            if 'img' in request.FILES:
                image_upload = upload(request.FILES['img'])
                validated_data['img'] = image_upload['secure_url']

            if 'cv' in request.FILES:
                cv_upload = upload(request.FILES['cv'], resource_type="raw")
                validated_data['cv'] = cv_upload['secure_url']

            if 'national_id_img' in request.FILES:
                national_id_upload = upload(request.FILES['national_id_img'])
                validated_data['national_id_img'] = national_id_upload['secure_url']

          return super().update(instance, validated_data)

class CompanyProfileSerializer(serializers.ModelSerializer):
    logo=serializers.ImageField(required=False)
    class Meta:
        model = Company
        fields = [
            'email', 
            'name',
            'est', 
            'industry', 
            'img',
            'location', 
            'phone_number',
            'logo'
            ]
        read_only_fields = ['email']
        
        def update(self, instance, validated_data):
            request = self.context.get('request')
            if request and hasattr(request, "FILES"):
                if 'img' in request.FILES:
                     image_upload = upload(request.FILES['img'])
                     validated_data['img'] = image_upload['secure_url']

            if 'logo' in request.FILES:
                logo_upload = upload(request.FILES['logo'])
                validated_data['logo'] = logo_upload['secure_url']

             
            return super().update(instance, validated_data) 



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
        if not user:
            raise serializers.ValidationError(_('Unable to authenticate with provided credentials'), code='authorization')
        attrs['user'] = user
        return attrs
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers
from .models import Company, Jobseeker

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
    class Meta:
        model = Jobseeker
        fields = [
            'email', 
            'name', 
            'dob', 
            'education', 
            'experience', 
            'cv', 
            'keywords',
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
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'email', 
            'name',
            'est', 
            'industry', 
            'img',
            'location', 
            'phone_number'
            ]
        read_only_fields = ['email']
        
        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance



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

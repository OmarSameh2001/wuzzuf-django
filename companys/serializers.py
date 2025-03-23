#serializer for company api view
from .models import Company

from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _
from rest_framework import serializers

class CompanySerializer(serializers.ModelSerializer):
    #serializer for user object
    class Meta:
        model = Company
        fields = ['email', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        #create and return company with encrypted pass
        return Company.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        #update and return user
        password = validated_data.pop('password', None)
        company = super().update(instance, validated_data)

        if password:
            company.set_password(password)
            company.save()

        return company


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'email', 'name', 'est', 'img', 'location', 'phone_number', 'industry', 'is_company',
        ]
        read_only_fields = ['email']

class AuthTokenSerializer(serializers.Serializer):
    #serializer for user auth token
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input-type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        #validate and authenticate user
        email = attrs.get('email')
        password = attrs.get('password')
        try:
            company = Company.objects.get(email=email)
        except Company.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials', code='authorization')

        # Manually check password
        if not company.check_password(password):
            raise serializers.ValidationError('Invalid credentials', code='authorization')

        attrs['company'] = company
        return attrs
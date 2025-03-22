#serializer for user api view

from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    #allow user to upload cv
    cv = serializers.FileField(required=False) 
    #serializer for user object
    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'password', 'name','cv']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        #create and return user with encrypted pass
        cv_file = validated_data.pop('cv', None)
        user=get_user_model().objects.create_user(**validated_data)
        if cv_file:
            user.cv = cv_file
            user.save()
        return user
    
    def update(self, instance, validated_data):
        #update and return user
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            'email', 'username', 'name', 'dob', 'education', 'experience', 
            'cv', 'img', 'location', 'keywords', 'national_id', 'national_id_img', 
            'phone_number', 'is_company'
        ]
        read_only_fields = ['email', 'username']

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
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = ('unable to authenticate with provided cridentials')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs

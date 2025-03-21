#serializer for user api view

from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    #serializer for user object
    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        #create and return user with encrypted pass
        return get_user_model().objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        #update and return user
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user
    

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

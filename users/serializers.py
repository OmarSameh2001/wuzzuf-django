#serializer for user api view

from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _
from rest_framework import serializers
from cloudinary.uploader import upload, destroy



class UserSerializer(serializers.ModelSerializer):
   
    #serializer for user object
    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        #create and return user with encrypted pass
       
        user=get_user_model().objects.create_user(**validated_data)
        
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

     #allow user to upload cv
    #cv = serializers.FileField(write_only=True)
    cv_url = serializers.SerializerMethodField(read_only=True) 
    profile_image_url = serializers.SerializerMethodField()
    class Meta:
        model = get_user_model()
        fields = [
            'email', 'username', 'name', 'dob', 'education', 'experience', 
            'cv', 'cv_url', 'img', 'location', 'keywords', 'national_id', 'national_id_img', 
            'phone_number', 'is_company'
        ]
        read_only_fields = ['email', 'username']
        

    def get_cv_url(self, obj):
        return obj.cv.url if obj.cv else None

    def get_profile_image_url(self, obj):
        return obj.profile_image.url if obj.profile_image else None


class UserCVSerializer(serializers.ModelSerializer):
    cv = serializers.FileField(write_only=True)
    cv_url = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['cv', 'cv_url']

    def get_cv_url(self, obj):
        return obj.cv.url if obj.cv else None

    def update(self, instance, validated_data):
        cv_file = validated_data.pop('cv', None)

        if cv_file:
            # Delete old CV if exists
            if instance.cv:
                destroy(instance.cv.public_id, resource_type="raw")

            upload_result = upload(cv_file, resource_type="raw")
            instance.cv = upload_result['public_id']
            instance.save()

        return instance



class UserProfileImageSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['profile_image', 'profile_image_url']

    def get_profile_image_url(self, obj):
        return obj.profile_image.url if obj.profile_image else None

    def update(self, instance, validated_data):
        image_file = validated_data.pop('profile_image', None)

        if image_file:
            # Delete old image if exists
            if instance.profile_image:
                destroy(instance.profile_image.public_id, resource_type="image")

            upload_result = upload(image_file)
            instance.profile_image = upload_result['public_id']
            instance.save()

        return instance



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

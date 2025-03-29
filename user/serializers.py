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
        return User.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class JobseekerProfileSerializer(serializers.ModelSerializer):
    cv = serializers.FileField(required=False)
    national_id_img = serializers.ImageField(required=False)
    # img = serializers.ImageField(required=False) shofy de feen kda !!!!!!!!!!!
    class Meta:
        model = Jobseeker
        fields = ['email', 'password', 'name', 'dob', 'education', 'experience', 'phone_number', 'cv', 'national_id', 'national_id_img', 'skills'] #, 'keywords'
        read_only_fields = ['national_id']


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['email', 'password', 'name','est', 'industry', 'location', 'phone_number']


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





# from django.contrib.auth import get_user_model, authenticate
# from django.utils.translation import gettext as _
# from rest_framework import serializers
# from .models import Jobseeker, Company

# User = get_user_model()

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["email", "username", "password", "name", "user_type"]
#         extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

#     def create(self, validated_data):
#         return User.objects.create(**validated_data)
#         # return User.objects.create_user(**validated_data)

#     def update(self, instance, validated_data):
#         password = validated_data.pop("password", None)
#         user = super().update(instance, validated_data)
#         if password:
#             user.set_password(password)
#             user.save()
#         return user


# class JobseekerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Jobseeker
#         fields = [
#             "email", "username", "name", "dob", "education", "experience", "cv", "img", 
#             "location", "keywords", "national_id", "national_id_img", "phone_number", "user_type"
#         ]
#         read_only_fields = ["email", "username", "user_type"]


# class CompanySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Company
#         fields = ["email", "username", "name", "est", "industry", "img", "location", "phone_number", "user_type"]
#         read_only_fields = ["email", "username", "user_type"]


# class AuthTokenSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(
#         style={"input-type": "password"},
#         trim_whitespace=False,
#     )

#     def validate(self, attrs):
#         email = attrs.get("email")
#         password = attrs.get("password")
#         user = authenticate(
#             request=self.context.get("request"), username=email, password=password
#         )
        
#         if not user:
#             raise serializers.ValidationError("Unable to authenticate with provided credentials", code="authorization")

#         attrs["user"] = user
#         return attrs

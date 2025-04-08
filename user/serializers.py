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
    id = serializers.CharField(read_only=True)
    cv = serializers.CharField(allow_blank=True, required=False)
    img = serializers.ImageField( allow_null=True ,required=False)
    national_id_img = serializers.ImageField( allow_null=True ,required=False)

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
            'cv', 
            'img', 
            'national_id', 
            'national_id_img', 
            'location', 
            'phone_number',
            'skills',
            'user_type'
        ]
        read_only_fields = ['email']


    # def update(self, instance, validated_data):
    #         # Update the fields for the jobseeker model
    #       request = self.context.get('request')
    #       if request and hasattr(request, "FILES"):
    #         if 'img' in request.FILES:
    #             image_upload = upload(request.FILES['img'])
    #             validated_data['img'] = image_upload['secure_url']

    #         if 'cv' in request.FILES:
    #             cv_upload = upload(request.FILES['cv'], resource_type="raw")
    #             validated_data['cv'] = cv_upload['secure_url']

    #         if 'national_id_img' in request.FILES:
    #             national_id_upload = upload(request.FILES['national_id_img'])
    #             validated_data['national_id_img'] = national_id_upload['secure_url']

    #       return super().update(instance, validated_data)
    def update(self, instance, validated_data):
        # Handle image fields (accept full URL directly)
            instance.img = validated_data.get('img', instance.img)
            instance.national_id_img = validated_data.get('national_id_img', instance.national_id_img)

            # Handle CV upload (if sent as a file)
            request = self.context.get('request')
            if request and hasattr(request, "FILES") and 'cv' in request.FILES:
                cv_upload = upload(request.FILES['cv'], resource_type="raw")
                validated_data['cv'] = cv_upload['secure_url']

            # Update other fields
            instance.name = validated_data.get('name', instance.name)
            instance.about = validated_data.get('about', instance.about)
            instance.dob = validated_data.get('dob', instance.dob)
            instance.education = validated_data.get('education', instance.education)
            instance.experience = validated_data.get('experience', instance.experience)
            instance.cv = validated_data.get('cv', instance.cv)  # Use the uploaded URL if available
            instance.national_id = validated_data.get('national_id', instance.national_id)
            instance.location = validated_data.get('location', instance.location)
            instance.phone_number = validated_data.get('phone_number', instance.phone_number)
            instance.skills = validated_data.get('skills', instance.skills)

            # Save the updated instance
            instance.save()
            return instance
class CompanyProfileSerializer(serializers.ModelSerializer):
    logo=serializers.ImageField(required=False)
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
            'logo'
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

                if 'national_id_img' in request.FILES:
                    national_id_upload = upload(request.FILES['national_id_img'])
                    validated_data['national_id_img'] = national_id_upload['secure_url']
            
            # Now update the instance with the validated data
            # Ensure the instance fields are updated with validated data
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            # Save the updated instance to persist the changes
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
        print(email,password, user)
        if not user:
            raise serializers.ValidationError(_('Unable to authenticate with provided credentials'), code='authorization')
        attrs['user'] = user
        return attrs
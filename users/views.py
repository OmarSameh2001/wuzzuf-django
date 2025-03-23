from django.shortcuts import render
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema
from .serializers import (
    UserSerializer,
    AuthTokenSerializer,
    UserProfileSerializer
    )
from rest_framework.parsers import MultiPartParser, FormParser
from cloudinary.uploader import upload, destroy
from rest_framework.response import Response
# Create your views here.
#views for user api
class CreateUserView(generics.CreateAPIView):
    #create new user in system
    serializer_class = UserSerializer
    #3l4an allow file upload
    parser_classes = (MultiPartParser, FormParser)

class CreateTokenView(ObtainAuthToken):
    #create new authtoken for user
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class ManageUserView(generics.RetrieveUpdateAPIView):
    #manage authenticated user
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        #retrive and return authenticated user
        return self.request.user
    

class UpdateUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 

    def get_object(self):
        return self.request.user
    
    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        methods=['PATCH', 'PUT']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        methods=['PUT']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        validated_data = request.data.copy()

        # Handle CV Upload
        cv_file = request.FILES.get("cv")
        if cv_file:
            if not cv_file.name.lower().endswith(".pdf"):
                return Response({"error": "Only PDF files are allowed."}, status=400)
            if user.cv:
                destroy(user.cv.public_id, resource_type="raw")
            upload_result = upload(cv_file, resource_type="raw")
            validated_data["cv"] = upload_result["public_id"]
            validated_data["cv_url"] = upload_result["secure_url"]
        elif "cv" in validated_data and validated_data["cv"] is None:
            if user.cv:
                destroy(user.cv.public_id, resource_type="raw")
            validated_data["cv"] = None
            validated_data["cv_url"] = None

        # Handle Profile Image Upload
        profile_img = request.FILES.get("img")
        if profile_img:
            if user.img:
                destroy(user.img.public_id, resource_type="image")
            img_result = upload(profile_img, resource_type="image")
            validated_data["img"] = img_result["public_id"]
        elif "img" in validated_data and validated_data["img"] is None:
            if user.img:
                destroy(user.img.public_id, resource_type="image")
            validated_data["img"] = None

        serializer = self.get_serializer(user, data=validated_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data) 
     
   
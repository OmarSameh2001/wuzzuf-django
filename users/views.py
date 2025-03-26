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
from cloudinary.uploader import upload
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import requests
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .serializers import UserSerializer



# Create your views here.
#views for user api
class CreateUserView(generics.CreateAPIView):
    #create new user in system
    serializer_class = UserSerializer

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
    # permission_classes = [permissions.IsAuthenticated]
    
    permission_classes = [IsAuthenticated]
    #ll file upload
    parser_classes = [MultiPartParser, FormParser]
    def get_object(self, request):
        serializer = UserProfileSerializer(request.user)
        print (serializer.data)
        print (request.user)
        return Response(serializer.data)
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()

        # Upload image to Cloudinary
        if 'img' in request.FILES:
            image_upload = upload(request.FILES['img'])
            data['img'] = image_upload['secure_url']

        # Upload CV to Cloudinary
        if 'cv' in request.FILES:
            cv_upload = upload(request.FILES['cv'], resource_type="raw")
            data['cv'] = cv_upload['secure_url']

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
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

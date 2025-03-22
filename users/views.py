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
    permission_classes = [permissions.IsAuthenticated]

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

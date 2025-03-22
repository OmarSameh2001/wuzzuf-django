from django.shortcuts import render
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from .serializers import (
    UserSerializer,
    AuthTokenSerializer
    )
from rest_framework.parsers import MultiPartParser, FormParser

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
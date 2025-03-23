from django.shortcuts import render
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema
from .serializers import (
    CompanySerializer,
    AuthTokenSerializer,
    CompanyProfileSerializer
    )

# Create your views here.
#views for company api
class CreateCompanyView(generics.CreateAPIView):
    #create new user in system
    serializer_class = CompanySerializer

class CreateTokenView(ObtainAuthToken):
    #create new authtoken for user
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class ManageCompanyView(generics.RetrieveUpdateAPIView):
    #manage authenticated user
    serializer_class = CompanySerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        #retrive and return authenticated company
        return self.request.company
    

class UpdateCompanyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CompanyProfileSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.company
    
    @extend_schema(
        request=CompanyProfileSerializer,
        responses={200: CompanyProfileSerializer},
        methods=['PATCH', 'PUT']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        request=CompanyProfileSerializer,
        responses={200: CompanyProfileSerializer},
        methods=['PUT']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

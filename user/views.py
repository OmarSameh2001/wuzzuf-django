from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import UserSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from cloudinary.uploader import upload
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser

User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class JobseekerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(user_type=User.UserType.JOBSEEKER)
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(user_type=User.UserType.COMPANY)
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]


class CustomAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_type": user.user_type,
            "email": user.email
        })
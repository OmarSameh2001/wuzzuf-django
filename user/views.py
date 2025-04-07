from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import UserSerializer, OTPVerificationSerializer,  JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import Company, Jobseeker, User
from django_filters.rest_framework import DjangoFilterBackend
from cloudinary.uploader import upload
from rest_framework.decorators import api_view
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .utils import send_otp_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import HttpResponse
import smtplib

User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()  # Create user instance
        otp = self.send_otp(user.email)  # Send OTP after registration

        if otp:  # Ensure OTP is valid before saving
            user.otp_digit = otp
            user.save()
        else:
            print(f"Failed to generate OTP for {user.email}")

    def send_otp(self, email):        
        otp = send_otp_email(email)  
        if otp is None:
            print(f"OTP sending failed for {email}")  # Debugging
        return otp  # Return OTP so it can be saved
        # user = User.objects.get(email=email)
        # user.otp_digit = otp
        # user.save()


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class JobseekerViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.JOBSEEKER)
    queryset = Jobseeker.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]
    #ll file upload
    parser_classes = [MultiPartParser, FormParser]
    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        # return super().partial_update(request, *args, **kwargs)
        user = self.get_object()
        data = request.data.copy()

        if 'img' in request.FILES:
            image_upload = upload(request.FILES['img'])
            data['img'] = image_upload['secure_url']

        if 'cv' in request.FILES:
            cv_upload = upload(request.FILES['cv'], resource_type="raw")
            data['cv'] = cv_upload['secure_url']

        if 'national_id_img' in request.FILES:
            national_id_upload = upload(request.FILES['national_id_img'])
            data['national_id_img'] = national_id_upload['secure_url']

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class CompanyViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.COMPANY)
    queryset = Company.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        # return super().partial_update(request, *args, **kwargs)
        user = self.get_object()
        data = request.data.copy()

        if 'img' in request.FILES:
            image_upload = upload(request.FILES['img'])
            data['img'] = image_upload['secure_url']

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class JobseekerListView(generics.ListAPIView):
    queryset = Jobseeker.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allows public to view but restricts modifications
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'education', 'skills', 'location']  # Exact match filters
    search_fields = ['name', 'education', 'skills','location']  # Partial match search


class VerifyOTPView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,  # Automatically pulls from serializer
        responses={
            status.HTTP_200_OK: openapi.Response('OTP verified successfully!'),
            status.HTTP_400_BAD_REQUEST: openapi.Response('Invalid OTP'),
            status.HTTP_404_NOT_FOUND: openapi.Response('User not found')
        }
    )
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            print(email, otp)  # Check if this prints now

            try:
                user = User.objects.get(email=email)
                if user.otp_digit == otp:
                    user.verify_status = True
                    user.is_active = True  # Activate user account
                    user.otp_digit = None  # Clear OTP after successful verification
                    user.save()
                    return Response({'message': 'OTP verified successfully!'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Debugging part - print the serializer errors
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def test_email_connection(request):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('hebagassem911@gmail.com', 'jucz gujg xwxx ewln')
        return HttpResponse("Connection Successful!")
    except Exception as e:
        return HttpResponse(f"Failed to connect: {e}")

class CustomAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not user.verify_status:
            return Response({"error": "Please verify your OTP before logging in."}, status=status.HTTP_400_BAD_REQUEST)
        
        token, _ = Token.objects.get_or_create(user=user)

        user_data = {
            "token": token.key,
            "id": user.id,
            "user_type": user.user_type,
            "email": user.email,
            "name": user.name,
            "img": user.img,
            "location": user.location,
            "phone_number": user.phone_number,
        }

        # Add extra fields for Jobseekers
        if user.user_type == User.UserType.JOBSEEKER:
            user_data.update({
                "dob": user.dob,
                "education": user.education,
                "experience": user.experience,
                "cv": user.cv,
                "keywords": user.keywords,
                "skills": user.skills,
            })

        # Add extra fields for Companies
        elif user.user_type == User.UserType.COMPANY:
            user_data.update({
                "est": user.est,
                "industry": user.industry,
            })

        return Response(user_data)
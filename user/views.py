from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from cloudinary.uploader import upload
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from .filters import JobseekerFilter
from rest_framework import status
from .utils import send_otp_email
from .serializers import UserSerializer, OTPVerificationSerializer,PasswordResetConfirmSerializer, PasswordResetRequestSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer
from .models import Company, Jobseeker
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import smtplib
from django.contrib.auth.tokens import default_token_generator


User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        # Save the user first
        user = serializer.save()

        # Now send OTP email and update user with OTP
        otp = self.send_otp(user.email)

        if user.otp_digit == otp:
            print(f"Stored OTP: {user.otp_digit}, Entered OTP: {otp}")


        if otp:  # Ensure OTP is valid before saving
            user.otp_digit = otp
            user.save()
            print(f"Saved OTP for {user.email}: {user.otp_digit}")


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
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class JobseekerViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.JOBSEEKER)
    # queryset = Jobseeker.objects.all()
    queryset = Jobseeker.objects.all().order_by('id')
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]
    #ll file upload
    parser_classes = [MultiPartParser, FormParser]
    # cv = serializers.FileField()
    # cv = serializers.FileField()
    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
            # Debug: Check request.FILES
        print("🟡 request.FILES:", request.FILES)
        user = self.get_object()
        data = request.data.copy() if not isinstance(request.data, dict) else request.data

        try:
            # Handle image uploads
            if 'img' in request.FILES:
                image_upload = upload(request.FILES['img'])
                data['img'] = image_upload['secure_url']
                # data['img']=data['img']
                
            # # Handle CV upload
            # if 'cv' in request.FILES:
            #     print(request.FILES['cv'])
            #     cv_upload = upload(request.FILES['cv'], resource_type="raw")
            #     data['cv'] = cv_upload['secure_url']
            #     print("cv_upload", data['cv'])
            # elif 'cv' in data and data['cv'] == '':  # Check for empty string
            #     data['cv'] = None    
                
                
              # Handle CV upload
            if 'cv' in request.FILES:
               print(request.FILES['cv'])
               cv_upload = upload(request.FILES['cv'], resource_type="raw")
               data['cv'] = cv_upload['secure_url']
            elif 'cv' in data and data['cv'] == '':  # Check for empty string
                data['cv'] = None    
    

            # Handle national ID image upload
            if 'national_id_img' in request.FILES:
                    national_id_upload = upload(request.FILES['national_id_img'])
                    data['national_id_img'] = national_id_upload['secure_url']
                    # data['national_id_img'] = data['national_id_img']
             # Create or update serializer instance
            serializer = self.get_serializer(user, data=data, partial=True)
            print('data', data)
            # Validate serializer
            if not serializer.is_valid():
                print("🔴 Serializer Errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Save the updated instance
            job = serializer.save()  # This will save the instance
            print("job", job.cv)
            self.perform_update(serializer)

            # Debug: Print the updated data
            print("🔵 serializer.data:", serializer.data)

            return Response(serializer.data)
    
        except Exception as e:
          print(f"🔴 Error during update: {str(e)}")
        #   print(serializer)
          return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class CompanyViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.COMPANY)
    queryset = Company.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]
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

        if 'logo' in request.FILES:
            logo_upload = upload(request.FILES['logo'])
            data['logo'] = logo_upload['secure_url']   

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)



# class CompleteProfileView(generics.UpdateAPIView):
#     permission_classes = [IsAuthenticated]

#     def get_serializer_class(self):
#         if self.request.user.user_type == User.UserType.JOBSEEKER:
#             return JobseekerProfileSerializer
#         return CompanyProfileSerializer

#     def get_object(self):
#         return self.request.user

class JobSeekerPagination(PageNumberPagination):
     page_size = 5  # Adjust as needed
     page_size_query_param = 'page_size'
     max_page_size = 100

class JobseekerListView(generics.ListAPIView):
    queryset = Jobseeker.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    pagination_class = JobSeekerPagination
    filterset_class = JobseekerFilter


class VerifyOTPView(APIView):
    # permission_classes = [IsAuthenticated]

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
                    # user.otp_digit = None  # Clear OTP after successful verification
                    user.save()
                    return Response({'message': 'OTP verified successfully!'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Debugging part - print the serializer errors
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetRequestView(APIView):
    """API View to send password reset email"""

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.send_password_reset_email()
            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """API View to reset password"""

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPasswordResetTokenView(APIView):
    """Endpoint to get the token for the user based on their email"""

    def get(self, request, email):  # <-- Get email from URL
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            return Response({'token': token}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=400)

@api_view(['POST'])
def check_email_exists(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(email=email).exists():
        return Response({"exists": True, "error": "Email already exists"}, status=status.HTTP_200_OK)
    return Response({"exists": False, "message": "Email is available"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def check_username_exists(request):
    username = request.data.get("username")
    if not username:
        return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({"exists": True, "error": "Username already exists"}, status=status.HTTP_200_OK)
    return Response({"exists": False, "message": "Username is available"}, status=status.HTTP_200_OK)



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


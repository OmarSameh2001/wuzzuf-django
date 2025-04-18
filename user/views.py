from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from django_filters.rest_framework import DjangoFilterBackend
from cloudinary.uploader import upload
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from .filters import JobseekerFilter, CompanyFilter
from rest_framework import status
from .utils import send_otp_email
from .serializers import UserSerializer, OTPVerificationSerializer,PasswordResetConfirmSerializer, PasswordResetRequestSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer, ItianSerializer
from .models import Company, Jobseeker, Itian
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import smtplib
from django.contrib.auth.tokens import default_token_generator
from rest_framework.exceptions import ValidationError

from .filters import JobseekerFilter
from rest_framework.decorators import action


import csv
from io import StringIO
import pandas as pd
from django.core.validators import EmailValidator
from .models import validate_egyptian_national_id


User = get_user_model()

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email', 'name', 'user_type']
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['get'])
    def company(self, request):
        queryset = Company.objects.filter(is_verified=False, is_active=True)
        filterset = CompanyFilter(request.query_params, queryset=queryset)
        page_size = request.query_params.get('page_size', 10)
        page = request.query_params.get('page', 1)
        serializer = CompanyProfileSerializer(filterset.qs, many=True)
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(serializer.data, request)
        return paginator.get_paginated_response(result_page)

    @action(detail=False, methods=['patch'])
    def verify_company(self, request):
        id = request.query_params.get('id')
        company = Company.objects.filter(id=id).first()

        print("company", id)
        if not company:
            return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        company.is_verified = True
        company.save()
        return Response({"message": "Company verified successfully"})
    
    @action(detail=False, methods=['get'])
    def itian(self, request):
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        itians = Itian.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(itians, request)
        serializer = ItianSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_itian(self, request):
        file = request.FILES.get('file', None)
        print("file", file)
        if not file:
            email = request.data.get('email')
            national_id = request.data.get('national_id')
            if not email or not national_id:
                return Response({"error": "Email and national_id are required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                # Validate email format
                EmailValidator()(email)
                validate_egyptian_national_id(str(national_id))
                if User.objects.filter(email=email).exists():
                    return Response({"error": f"User {email} already exists."}, status=status.HTTP_400_BAD_REQUEST)
                if Itian.objects.filter(email=email, national_id=national_id).exists():
                    return Response({"error": f"User {email} already exists."}, status=status.HTTP_400_BAD_REQUEST)
                Itian.objects.create(
                    email=email,
                    national_id=national_id,
                )
                return Response({"message": f"User {email} created successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f"Error creating user {email}: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            file_name = file.name
            try:
                if file_name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file)
                elif file_name.endswith('.csv'):
                    try:
                        df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(file, encoding='ISO-8859-1', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            df = pd.read_csv(file, encoding='Windows-1252', on_bad_lines='skip')
                else:
                    return Response({"error": 'Unsupported file format. Please upload a CSV or Excel file.'}, status=status.HTTP_400_BAD_REQUEST)

                if 'email' not in df.columns or 'national_id' not in df.columns:
                    return Response({"error": 'File must contain "email" and "national_id" columns'}, status=status.HTTP_400_BAD_REQUEST)

                num = 0
                bad = 0
                for index, row in df.iterrows():
                    email = row['email']
                    national_id = row['national_id']
                    try:
                        # Validate email format
                        EmailValidator()(email)
                        validate_egyptian_national_id(str(national_id))
                        if Itian.objects.filter(email=email, national_id=national_id).exists():
                            bad += 1
                            continue

                        Itian.objects.create(
                            email=email,
                            national_id=national_id,
                        )
                        num += 1
                    except Exception as e:
                        print({"error": f"Error creating user {email}: {e}"})
                        bad += 1
                        continue

                if num > 0: 
                    if bad > 0:
                        return Response({"message": f"Successfully created {num} users. {bad} users failed."}, status=status.HTTP_201_CREATED)
                    return Response({"message": f"Successfully created {num} users."}, status=status.HTTP_201_CREATED)
                elif bad > 0:
                    return Response({"message": f"{bad} users failed validation."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "No new users created."}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": f"Error processing file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_itian(self, request):
        id = request.query_params.get('id')
        itian = Itian.objects.filter(id=id).first()
        if not itian:
            return Response({"message": "Itian not found"}, status=status.HTTP_404_NOT_FOUND)
        itian.delete()  
        return Response({"message": "Itian deleted successfully"})


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        print("serializer.validated_data", serializer.validated_data)
        if serializer.validated_data['user_type'] == User.UserType.JOBSEEKER:
            if Itian.objects.filter(
                email=serializer.validated_data['email'],
                national_id=serializer.validated_data['national_id']
            ).exists():
                print("Itian found")
            else:
                print("Itian not found")
                raise ValidationError({"error": "Itian not found contact iti support"})
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

class DynamicUserSchema(AutoSchema):
    def get_serializer(self, path, method):
        view = self.view
        user = getattr(view.request, 'user', None)
        if user and user.user_type == 'company':
            return CompanyProfileSerializer()
        return JobseekerProfileSerializer()

class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]
    schema = DynamicUserSchema() 

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        user = self.request.user
        if user.user_type == 'JOBSEEKER':
            return JobseekerProfileSerializer
        elif user.user_type == 'COMPANY':
            return CompanyProfileSerializer
        else:
            return JobseekerProfileSerializer  # default fallback


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
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if data.get('national_id') == '':
            data['national_id'] = None


        try:
            # Handle image uploads
            if 'img' in request.FILES:
                image_upload = upload(request.FILES['img'])
                data['img'] = image_upload['secure_url']
                # data['img']=data['img']
        
                
              # Handle CV upload
            if 'cv' in request.FILES:
               print(request.FILES['cv'])
               cv_upload = upload(request.FILES['cv'], resource_type="raw")
               cv_url = cv_upload['secure_url']
               
               if not cv_url.endswith('.pdf'):
                   cv_url= cv_upload['secure_url']+".pdf"
                  
               data['cv'] = cv_url
               print("cv_upload", cv_url)
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
    @action(methods=["post"], detail=False)
    def get_talents(self, request, *args, **kwargs):
        # print(request.data)
        id = int(request.query_params.get('id'))
        print("id", id)
        talent = Jobseeker.objects.filter(id=id).first()
        print("talent", talent)
        serializer = JobseekerProfileSerializer(talent)
        return Response(serializer.data)



class CompanyViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.COMPANY)
    queryset = Company.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
     # Add filter backends and pagination for the get_talents action
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = JobseekerFilter
    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        # return super().partial_update(request, *args, **kwargs)
        user = self.get_object()
        data = request.data.copy()
       
       
        if 'img' in request.FILES:
            image_upload = upload(request.FILES['img'])
            data['img'] = image_upload['secure_url']

        # if 'logo' in request.FILES:
        #     logo_upload = upload(request.FILES['logo'])
        #     data['logo'] = logo_upload['secure_url']   

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

        # Check if user is active before proceeding
        if not user.is_active:
            return Response({"error": "User is not active"}, status=status.HTTP_400_BAD_REQUEST)

        # Check for OTP verification status (for Jobseeker)
        if not user.verify_status and user.user_type == User.UserType.JOBSEEKER:
            return Response({"error": "Please verify your OTP before logging in."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get the authentication token
        token, _ = Token.objects.get_or_create(user=user)

        # Create response data
        user_data = {
            "token": token.key,
            "id": user.id,
            "user_type": user.user_type,
            "email": user.email,
            "name": user.name,
            "location": user.location,
            "phone_number": user.phone_number,
        }

        if not user.is_active:
            print("User is not active")
            return Response({"error": "User is not active"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.verify_status and user.user_type == User.UserType.JOBSEEKER:
            print("Jobseeker OTP not verified")
            return Response({"error": "Please verify your OTP before logging in."}, status=status.HTTP_400_BAD_REQUEST)


        # Check if the user is a superuser and update the user_type
        if user.is_superuser:
            user_data.update({"user_type": "admin"})

        # Add extra fields based on user type
        if user.user_type == User.UserType.JOBSEEKER:
            user_data.update({
                "dob": user.dob,
                "education": user.education,
                "experience": user.experience,
                "keywords": user.keywords,
                "skills": user.skills,
            })
        elif user.user_type == User.UserType.COMPANY:
            user_data.update({
                "est": user.est,
                "industry": user.industry,
            })

        return Response(user_data)



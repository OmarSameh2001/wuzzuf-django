from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from rest_framework import generics, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from django_filters.rest_framework import DjangoFilterBackend
from cloudinary.uploader import upload
from datetime import timedelta

from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from .filters import JobseekerFilter, CompanyFilter
from rest_framework import status
# from .utils import (send_otp_email, send_company_verification_email)
from .serializers import UserSerializer, OTPVerificationSerializer,PasswordResetConfirmSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer, ItianSerializer, UserQuestionsSerializer
from .models import Company, Jobseeker, Itian, UserQuestions
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import smtplib
from django.contrib.auth.tokens import default_token_generator
from rest_framework.exceptions import ValidationError
from .helpers import extract_dob_from_national_id

from .filters import JobseekerFilter
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone

import csv
from io import StringIO
import pandas as pd
from django.core.validators import EmailValidator
from .models import validate_egyptian_national_id
from rest_framework.filters import SearchFilter
from dotenv import load_dotenv
import os
import requests
from pymongo import MongoClient
from bson import ObjectId
load_dotenv()


FASTAPI_URL = os.getenv('FAST_API')
client = MongoClient(os.getenv('MONGO_URI'))
db = client['job_db']
rag_names_collection = db["rag_names"]
rag_collection=db["Rag"]
user_collection=db["user_cv_db"]
User = get_user_model()

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email', 'name', 'user_type']
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['get'])
    def company(self, request):
        queryset = Company.objects.filter(is_verified=False, is_active=True)
        search = request.query_params.get('search', None)
        filterset = CompanyFilter(request.query_params, queryset=queryset)
        page_size = request.query_params.get('page_size', 10)
        page = request.query_params.get('page', 1)

        # Filter by email or name if a search term is provided
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(name__icontains=search)
            )
        else:
            companies = Company.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = CompanyProfileSerializer(result_page, many=True)


        return paginator.get_paginated_response(serializer.data)


    @action(detail=False, methods=['patch'])
    def verify_company(self, request):
        id = request.query_params.get('id')
        company = Company.objects.filter(id=id).first()

        if not company:
            return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        
        company.is_verified = True
        company.save()

        # # Send verification email
        # email_sent = send_company_verification_email(company.email, company.name)

        # if email_sent:
        #     return Response({"message": "Company verified successfully and email sent."})
        # else:
        #     return Response({"message": "Company verified successfully but email failed to send."})

         # Inline call to Node.js mailer endpoint
        try:
            response = requests.post(
                os.getenv('MAIL_SERVICE') + "send-verification-email",
                json={"email": company.email, "name": company.name}
            )
            response.raise_for_status()
            print(f"Verification email sent to {company.email}")
            email_sent = True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            email_sent = False

        if email_sent:
            return Response({"message": "Company verified successfully and email sent."})
        else:
            return Response({"message": "Company verified successfully but email failed to send."})
    
    @action(detail=False, methods=['get'])
    def itian(self, request):
        search = request.query_params.get('search', '')
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        # Filter by email or national_id if a search term is provided
        if search:
            itians = Itian.objects.filter(
                Q(email__icontains=search) | Q(national_id__icontains=search)
            )
        else:
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

        user_type = serializer.validated_data.get('user_type')
        
        # Block admin registration
        if user_type == User.UserType.ADMIN:
            raise ValidationError({"error": "Admin registration is not allowed through this view."})

        if serializer.validated_data['user_type'] == User.UserType.JOBSEEKER:
            if Itian.objects.filter(
                email=serializer.validated_data['email'],
                national_id=serializer.validated_data['national_id']
            ).exists():
                print("Itian found")
                serializer.validated_data['dob'] = extract_dob_from_national_id(serializer.validated_data['national_id'])
            else:
                print("Itian not found")
                raise ValidationError({"error": "Itian not found contact iti support"})
        else:
            if Itian.objects.filter(
                email=serializer.validated_data['email'],
            ).exists():
                print("Itian found")
                raise ValidationError({"error": "Itian graduate can't be company"})

        # Save the user first
        user = serializer.save()
        if user.user_type == User.UserType.JOBSEEKER:
            user_collection.insert_one(
                    {"user_id": user.id, "email": user.email} 
                )

        # Now send OTP email and update user with OTP
        otp = self.send_otp(user.email, user.name)


        if otp is None:
            print(f"Failed to generate OTP for {user.email}")
            # Handle the failure case (e.g., raise error or notify user)
            raise ValidationError({"error": "Failed to send OTP email"})
        
        # else:
        #     print(f"OTP sent via Node.js: {otp}")

        # if user.otp_digit == otp:
        #     print(f"Stored OTP: {user.otp_digit}, Entered OTP: {otp}")

        # Ensure OTP is valid before saving
        user.otp_digit = otp
        user.otp_created_at = timezone.now()
        user.save()
        print(f"Saved OTP for {user.email}: {user.otp_digit}")

    def send_otp(self, email, name):                
        try:
            response = requests.post(os.getenv('MAIL_SERVICE') + "send-otp", json={"email": email, "name": name})
            response.raise_for_status()
            otp = response.json().get("otp")
            print(f"OTP sent via Node.js: {otp}")
            return otp
        except Exception as e:
            print(f"Error sending OTP via Node.js: {e}")
            return None


class ResendOTPView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")  # Assuming the user provides the email for resend

        if not email:
            raise ValidationError({"error": "Email is required"})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({"error": "User with this email does not exist"})

        # You can add logic to check OTP expiration, if needed
        if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() < 30:  # OTP expiry check, 5 minutes
            raise ValidationError({"error": "OTP has already been sent recently. Please wait before requesting again."})

        # Send new OTP
        otp = self.send_otp(user.email, user.name)

        if otp is None:
            print(f"Failed to generate OTP for {user.email}")
            raise ValidationError({"error": "Failed to send OTP email"})

        user.otp_digit = otp
        user.otp_created_at = timezone.now()
        user.save()

        return Response({"message": "OTP resent successfully. Check your email for the new OTP."}, status=status.HTTP_200_OK)

    def send_otp(self, email, name):
        try:
            response = requests.post(os.getenv('MAIL_SERVICE') + "send-otp", json={"email": email, "name": name})
            response.raise_for_status()
            otp = response.json().get("otp")
            print(f"OTP sent via Node.js: {otp}")
            return otp
        except Exception as e:
            print(f"Error sending OTP via Node.js: {e}")
            return None

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
    # schema = DynamicUserSchema() 

    def get_object(self):
        # print("self.request.user", self.request.user.img)
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
    # filterset_class = JobseekerFilter
    # def get_object(self):
    #     return self.request.user

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
        print("data", data['img'])
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
    queryset = Jobseeker.objects.filter(is_active=True)
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    pagination_class = JobSeekerPagination
    filterset_class = JobseekerFilter


class VerifyOTPView(APIView):
    # permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response('OTP verified successfully!'),
            status.HTTP_400_BAD_REQUEST: openapi.Response('Invalid OTP or expired'),
            status.HTTP_404_NOT_FOUND: openapi.Response('User not found')
        }
    )
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = str(serializer.validated_data['otp'])
            print(email, otp)  # Debugging

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if OTP data exists
            if not user.otp_digit or not user.otp_created_at:
                return Response({"error": "No OTP found. Please request again."}, status=status.HTTP_400_BAD_REQUEST)

            # Check OTP expiration (60 seconds)
            if timezone.now() > user.otp_created_at + timedelta(seconds=60):
                return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
            
             # Match the OTP (string comparison)
            if str(user.otp_digit) != otp:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            # If everything is valid, activate user
            user.is_active = True
            user.verify_status = True
            # user.otp_digit = None  # Optional: clear OTP
            user.save()
            return Response({'message': 'OTP verified successfully!'}, status=status.HTTP_200_OK)

        print(serializer.errors)
        print(f"OTP in DB: {user.otp_digit}")
        print(f"OTP entered: {otp}")
        print(f"Created at: {user.otp_created_at}, Now: {timezone.now()}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetRequestView(APIView):
    """API View to send password reset email"""

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        token = default_token_generator.make_token(user)
        reset_url = f"http://localhost:5173/reset-password/{user.email}?token={token}"

        # Send the password reset email using Node.js server
        try:
            response = requests.post(
                os.getenv('MAIL_SERVICE') + "send-password-reset",
                json={
                    "email": user.email,
                    "name": user.name,
                    "resetUrl": reset_url
                }
            )
            response.raise_for_status()
            print(f"Password reset email sent to {user.email}")

            # Optionally record timestamp
            if hasattr(user, 'password_reset_requests'):
                user.password_reset_requests.append(timezone.now().isoformat())
                user.save()

            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return Response({"error": "Failed to send password reset email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        # # Check for OTP verification status
        # if not user.verify_status:
        #     return Response({"error": "Please verify your OTP before logging in.", "otp": True}, status=status.HTTP_400_BAD_REQUEST)


        if not user.is_verified and user.user_type == User.UserType.COMPANY:
            return Response({"error": "Company account is pending verification. You will be able to access your account once the verification is complete."}, status=status.HTTP_400_BAD_REQUEST)
        
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
                "specialization": user.specialization
            })
        elif user.user_type == User.UserType.COMPANY:
            user_data.update({
                "est": user.est,
                "industry": user.industry,
            })

        return Response(user_data)

class UserQuestionsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class=UserQuestionsSerializer
    queryset=UserQuestions.objects.all()
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def post_rag(self, request):
        file = request.FILES.get('file', None)
        if not file:
            return Response({"message": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            rag_name = rag_names_collection.find_one({"name": file.name.replace(".pdf", "")})
            if rag_name:
                date = rag_name['created_at'].strftime('%Y-%m-%d %I:%M %p GMT')
                return Response({"message": f"Pdf with this name already uploaded on {date}"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                url = FASTAPI_URL + "/rag"
                response = requests.post(url, files={'pdf': file})
                if response.status_code != 200:
                    raise Exception(response.text)
                return Response(response.json())
            except Exception as e:
                print(f"Error processing PDF: {e}")
                return Response({"message": "PDF processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def get_rag(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        try:
            rag = list(rag_names_collection.find().sort('created_at', 1).skip((page - 1) * page_size).limit(page_size))
            for item in rag:
                item['_id'] = str(item['_id'])
            res = {'count': rag_names_collection.count_documents({}), 'page': page, 'page_size': page_size,'results': rag}
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        

    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_rag(self, request):
        try:
            print("request.query_params",  request.query_params["id"])
            if request.query_params.get("id"):
                rag = rag_names_collection.find_one({"_id": ObjectId(request.query_params["id"])})
            elif request.query_params.get("name"):
                rag = rag_names_collection.find_one({"name": request.query_params["name"]})
            else:
                return Response({"message": "No id or name provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not rag:
                return Response({"message": "Rag not found"}, status=status.HTTP_404_NOT_FOUND)

            result = rag_names_collection.delete_one({"_id": ObjectId(rag["_id"])})
            if result.deleted_count == 0:
                return Response({"message": "Rag not found"}, status=status.HTTP_404_NOT_FOUND)
            
            
            name = rag["name"]
            result_embed = rag_collection.delete_many({"metadata": name})
            if result_embed.deleted_count == 0:
                return Response({"message": "No embedded documents found for the given RAG"}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"message": "Rag and its embedded documents deleted successfully"})
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return Response({"message": "PDF processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_quota(self, request):
        limit = UserQuestions.objects.filter(user=request.user, date__gte=timezone.now() - timedelta(days=1)).first()
        if limit is not None:
            reset_time = limit.date + timedelta(days=1)
            if reset_time > timezone.now():
                return Response({"message": f"You have {5 -limit.questions} questions left, resets on {reset_time.strftime('%Y-%m-%d %I:%M %p GMT')}", "questions": 5-limit.questions, "date": reset_time.strftime('%Y-%m-%d %I:%M %p GMT')}, status=status.HTTP_200_OK)
        else:
            tomorow = timezone.now() + timedelta(days=1)
            return Response({"message": "You have 5 questions left", "questions": 5, "date": tomorow.strftime('%Y-%m-%d %I:%M %p GMT')}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def ask_chatbot(self, request):
        if not request.data["question"]:
            return Response({"message": "No question provided"}, status=status.HTTP_400_BAD_REQUEST)
        limit = UserQuestions.objects.filter(user=request.user, date__gte=timezone.now() - timedelta(days=1)).first()

        if limit is not None and limit.questions > 5:
            reset_time = limit.date + timedelta(days=1)
            if reset_time > timezone.now():
                date = reset_time.strftime("%Y-%m-%d %I:%M %p GMT")
                return Response({"message": f"You have reached the limit of 5 questions per day, resets on {date}"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = requests.post(FASTAPI_URL + "/ask_rag/?question=" + request.data["question"])
            if limit is not None and limit.questions < 5:
                limit.questions += 1
                limit.save()
            else:
                UserQuestions.objects.filter(user=request.user).delete()
                new_question = UserQuestions.objects.create(user=request.user, questions=1)
            return Response(response.json(), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error retriving answer": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        



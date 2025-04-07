from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, filters, serializers
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import UserSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import Company, Jobseeker
from django_filters.rest_framework import DjangoFilterBackend
from cloudinary.uploader import upload
from cloudinary.uploader import upload_resource
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from .filters import JobseekerFilter


User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Serializer Errors:", serializer.errors)  # Print validation errors
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_type": user.user_type
        })


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = JobseekerProfileSerializer
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
    # cv = serializers.FileField()
    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        # return super().partial_update(request, *args, **kwargs)
        print("🟡 request.FILES:", request.FILES)
        user = self.get_object()
        data = request.data.copy()

        if 'img' in request.FILES:
            image_upload = upload(request.FILES['img'])
            data['img'] = image_upload['secure_url']

        if 'cv' in request.FILES:
            print(request.FILES['cv'])
            cv_upload = upload(request.FILES['cv'], resource_type="raw")
            print("cv_upload", cv_upload['secure_url'])
            data['cv'] = cv_upload['secure_url']

        if 'national_id_img' in request.FILES:
            national_id_upload = upload(request.FILES['national_id_img'])
            data['national_id_img'] = national_id_upload['secure_url']

        print(data['cv'])
        serializer = self.get_serializer(user, data=data, partial=True)
        if not serializer.is_valid():
            print("🔴 Serializer Errors:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)



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




class CustomAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            print("Serializer Errors:", serializer.errors) 
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        user_data = {
            "id": user.id,
            "token": token.key,
            "user_type": user.user_type,
            "email": user.email,
            "name": user.name,
            "img": str(user.img) if user.img else None,
            "location": user.location,
            "phone_number": user.phone_number,
        }

        # Add extra fields for Jobseekers
        if user.user_type == User.UserType.JOBSEEKER:
            user_data.update({
                "dob": user.dob,
                "education": user.education,
                "experience": user.experience,
                "cv": str(user.cv) if user.cv else None,
                "skills": user.skills,
            })

        # Add extra fields for Companies
        elif user.user_type == User.UserType.COMPANY:
            user_data.update({
                "est": user.est,
                "industry": user.industry,
            })

        return Response(user_data)


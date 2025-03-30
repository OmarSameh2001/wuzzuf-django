from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import UserSerializer, JobseekerProfileSerializer, CompanyProfileSerializer, AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import Company, Jobseeker
from django_filters.rest_framework import DjangoFilterBackend


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
    # queryset = User.objects.filter(user_type=User.UserType.JOBSEEKER)
    queryset = Jobseeker.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class CompanyViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.filter(user_type=User.UserType.COMPANY)
    queryset = Company.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


# class CompleteProfileView(generics.UpdateAPIView):
#     permission_classes = [IsAuthenticated]

#     def get_serializer_class(self):
#         if self.request.user.user_type == User.UserType.JOBSEEKER:
#             return JobseekerProfileSerializer
#         return CompanyProfileSerializer

#     def get_object(self):
#         return self.request.user



class JobseekerListView(generics.ListAPIView):
    queryset = Jobseeker.objects.all()
    serializer_class = JobseekerProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allows public to view but restricts modifications
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'education', 'skills', 'location', 'keywords']  # Exact match filters
    search_fields = ['name', 'education', 'skills','location', 'keywords']  # Partial match search




class CustomAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        user_data = {
            "token": token.key,
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

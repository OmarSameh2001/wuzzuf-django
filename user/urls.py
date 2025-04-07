from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserCreateView, UserRetrieveUpdateView,
    JobseekerViewSet, CompanyViewSet, CustomAuthToken, JobseekerListView
    ,VerifyOTPView, test_email_connection
)

router = DefaultRouter()
router.register(r'jobseekers', JobseekerViewSet, basename='jobseeker')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', UserRetrieveUpdateView.as_view(), name='profile'),
    # path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('jobseekers/all/', JobseekerListView.as_view(), name='jobseeker-list'),
    path('test/', test_email_connection),
    path('token/', CustomAuthToken.as_view(), name='token'),
    path('', include(router.urls)),
]
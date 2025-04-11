from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserCreateView, UserRetrieveUpdateView,
    JobseekerViewSet, CompanyViewSet, CustomAuthToken, JobseekerListView,VerifyOTPView, GetPasswordResetTokenView
    ,PasswordResetRequestView, PasswordResetConfirmView, check_email_exists, check_username_exists
)

router = DefaultRouter()
router.register(r'jobseekers', JobseekerViewSet, basename='jobseeker')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', UserRetrieveUpdateView.as_view(), name='profile'),
    # path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path('password-reset/get-token/<str:email>/', GetPasswordResetTokenView.as_view(), name='get-reset-token'),   
    path('jobseekers/all/', JobseekerListView.as_view(), name='jobseeker-list'),
    path('check-email/', check_email_exists, name='check_email_exists'),
    path('check-username/', check_username_exists, name='check_username_exists'),
    path('token/', CustomAuthToken.as_view(), name='token'),
    path('', include(router.urls)),
]
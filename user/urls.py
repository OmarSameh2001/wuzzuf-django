from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserCreateView, UserRetrieveUpdateView,
    JobseekerViewSet, CompanyViewSet, CustomAuthToken, JobseekerListView
)

router = DefaultRouter()
router.register(r'jobseekers', JobseekerViewSet, basename='jobseeker')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', UserRetrieveUpdateView.as_view(), name='profile'),
    # path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path('jobseekers/all/', JobseekerListView.as_view(), name='jobseeker-list'),
    path('token/', CustomAuthToken.as_view(), name='token'),
    path('', include(router.urls)),
]
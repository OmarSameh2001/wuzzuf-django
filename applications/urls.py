from .views import  ApplicationViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', ApplicationViewSet, basename='applications')  # Ensure correct prefix

urlpatterns = [
    path('', include(router.urls)),  # REST API routes
]

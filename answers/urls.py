from .views import  AnswerViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', AnswerViewSet, basename='answers')  # Ensure correct prefix

urlpatterns = [
    path('', include(router.urls)),  # REST API routes
]

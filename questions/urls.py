from django.urls import path, include
from .views import QuestionViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"", QuestionViewSet, basename="classroom")

urlpatterns = [
    path("", include(router.urls)),
]
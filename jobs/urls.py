from jobs.viewsets import JobsViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_job_recommendations

router = DefaultRouter()
router.register("", JobsViewSet, basename="jobs")  # Ensure correct prefix

urlpatterns = [
    path("", include(router.urls)),  # REST API routes
    path("recom/<int:user_id>/", get_job_recommendations, name="job-recommendations"),
]

from jobs.viewsets import JobsViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_recommendationsView
from .views import ats_match

router = DefaultRouter()
router.register('', JobsViewSet, basename='jobs')  # Ensure correct prefix

urlpatterns = [
    path('', include(router.urls)),  # REST API routes
    path("recom/<int:user_id>/", get_recommendationsView, name="job-recommendations"),
    path("ats_match//<int:user_id>/", ats_match, name="ats-match"),

]

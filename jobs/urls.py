from django.urls import path , include 
from jobs.viewsets import JobsViewSet
from django.contrib import admin
from . import views
from rest_framework.routers import DefaultRouter
from .views import get_job_recommendations


router = DefaultRouter()

router.register('',JobsViewSet,basename='jobs')

urlpatterns = [
    path('',include(router.urls)),
     path("recom/<int:user_id>/", get_job_recommendations, name="job-recommendations"),
]

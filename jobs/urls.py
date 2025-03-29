from jobs.viewsets import JobsViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_recommendationsView
from .views import ats_match

router = DefaultRouter()
router.register('', JobsViewSet, basename='jobs') 

urlpatterns = [
    path('', include(router.urls)),  
    path("recom/<int:user_id>/", get_recommendationsView, name="job-recommendations"),
    path("ats/<int:user_id>/<int:job_id>", ats_match, name="ats-match"),

]

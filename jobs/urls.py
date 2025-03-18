from django.urls import path , include 
from jobs.viewsets import JobsViewSet
from django.contrib import admin
from . import views
from rest_framework.routers import DefaultRouter



router = DefaultRouter()

router.register('',JobsViewSet,basename='jobs')

urlpatterns = [
    path('',include(router.urls)),
    
]

from .models import Application
from .serializers import ApplicationSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from jobs.models import Job


@method_decorator(csrf_exempt, name='dispatch')
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer



from .models import Job
from .serializers import JobsSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import JobFilter

class JobPagination(PageNumberPagination):
     page_size = 5  # Adjust as needed
     page_size_query_param = 'page_size'
     max_page_size = 100
     
FASTAPI_URL = "http://127.0.0.1:8001/jobs"

@method_decorator(csrf_exempt, name='dispatch')
class JobsViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter
    pagination_class = JobPagination
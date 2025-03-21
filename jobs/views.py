from django.shortcuts import render
from .models import Jobs
from rest_framework import viewsets
from .serializers import JobsSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
import requests

FASTAPI_URL = "http://127.0.0.1:8001/recommend"

# Create your views here.




def get_job_recommendations(request, user_id):
    response = requests.get(f"{FASTAPI_URL}/{user_id}")
    return JsonResponse(response.json())





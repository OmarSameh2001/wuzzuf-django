from django.shortcuts import render
from .models import Job
from rest_framework import viewsets
from .serializers import JobsSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
import requests
from django.contrib.auth import get_user_model

User = get_user_model()

FASTAPI_URL = "http://127.0.0.1:8001/recom"

def get_recommendationsView(request , user_id):
    #user_skills = request.GET.get('user_skills', '')
    user = User.objects.get(id=user_id)
    user_skills = user.cv
    print(user_skills)

    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 5)

    fastapi_url = f"{FASTAPI_URL}/?user_skills={user_skills}&page={page}&page_size={page_size}"
    response = requests.get(fastapi_url)

    if response.status_code == 200:
        return JsonResponse(response.json())
    else:
        print(response)
        return JsonResponse({"error": "Failed to fetch recommendations"}, status=response.status_code)
# Create your views here.
def ats_match(request):
    if request.method == "POST":
        job_id = request.POST.get("job_id")
        cv_drive_link = request.POST.get("cv_drive_link")

        if not job_id or not cv_drive_link:
            return JsonResponse({"error": "Missing job_id or cv_drive_link"}, status=400)

        # Call FastAPI ATS endpoint
        response = requests.post(FASTAPI_URL, data={"job_id": job_id, "cv_drive_link": cv_drive_link})
        
        if response.status_code == 200:
            return JsonResponse(response.json(), status=200)
        else:
            return JsonResponse({"error": "FastAPI error", "details": response.json()}, status=response.status_code)

    return JsonResponse({"error": "Invalid request"}, status=400)

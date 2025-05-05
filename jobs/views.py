from django.shortcuts import render
from .models import Job
from rest_framework import viewsets
from .serializers import JobsSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
import requests
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from .models import Job
User = get_user_model()
import os
from dotenv import load_dotenv
load_dotenv()

FASTAPI_URL = os.environ.get("FAST_API")

# def get_recommendationsView(request , user_id ,):
#     #user_skills = request.GET.get('user_skills', '')
#     print(user_id)
#     user = User.objects.get(id=user_id)
#     print("user",user)
#     cv_url = user.cv
#     print(cv_url)

#     page = int(request.GET.get('page', 1))
#     page_size = int(request.GET.get('page_size', 5))

#     # fastapi_url = f"{FASTAPI_URL}/?user_skills={user_skills}&page={page}&page_size={page_size}"
#     fastapi_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}&page={page}&page_size={page_size}"
#     print(fastapi_url)
#     response = requests.get(fastapi_url)

#     if response.status_code == 200:
#         data = response.json()
#         total_results = data.get("total_results", 0)
#         total_pages = (total_results + page_size - 1) // page_size # Calculate total pages
        
#         return JsonResponse({
#             "page": page,
#             "page_size": page_size,
#             "total_pages": (total_results + page_size - 1),
#             "total_results": total_results,
#             "recommendations": data.get("recommendations", [])
#         })
#     else:
#         print(response)
#         return JsonResponse({"error": "Failed to fetch recommendations"}, status=response.status_code)
# Create your views here.
def get_recommendationsView(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        cv_url = user.cv
        
        if not cv_url:
            return JsonResponse({"error": "User has no CV uploaded"}, status=400)

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 5))

        fastapi_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}&page={page}&page_size={page_size}"
        print (fastapi_url)
        try:
            response = requests.get(fastapi_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            total_results = data.get("total_results", 0)
            total_pages = (total_results + page_size - 1) // page_size
             
            return JsonResponse({
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_results": total_results,
                "recommendations": data.get("recommendations", [])
            })
            
        except requests.exceptions.RequestException as e:
            error_msg = f"FastAPI service error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    error_msg = f"FastAPI error: {error_detail}"
                except:
                    error_msg = f"FastAPI error: {e.response.text}"
            return JsonResponse({"error": error_msg}, status=500)
            
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

def ats_match(request, user_id, job_id):
    print("user_id", user_id)
    print("job_id", job_id)
    try:
        user = User.objects.get(id=user_id)
        print("user", user)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    try:
        job = Job.objects.get(id=job_id)
        print("job", job)
    except Job.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)

    if not user.cv:
            # 3ayza  haga ttla3 f el front msg en el cv not found => ta2reban kda    
           return JsonResponse({"error": "User CV not found", "message": "Please upload a CV before applying."}, status=400)

    fastapi_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
    print("fastapi_url", fastapi_url)

    cv_url = str(user.cv) if user.cv else None
    print("cv_url", cv_url)
   
    payload = {
        "cv_url": cv_url,
        "job_id": job.id,
        # "job_title": job.title,
        # "job_description": job.description
    }
    print("payload", payload)

    try:
        response = requests.post(fastapi_url, json=payload, timeout=30)

        print("response", response)
        response_data = response.json()
        print("response_data", response_data)
        if not isinstance(response_data, dict):
            return JsonResponse({"error": "Unexpected response format from FastAPI"}, status=500)

        return JsonResponse(response_data, status=200)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": "FastAPI request failed", "details": str(e)}, status=500)
def get_talentsView(request, job_id):
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 5))
        
        fastapi_url = f"{FASTAPI_URL}/top_talents?job_id={job_id}&page={page}&page_size={page_size}"
        print(fastapi_url)
        
        try:
            response = requests.get(fastapi_url, timeout=10)
            # response.raise_for_status()
            data = response.json()
            
            return JsonResponse({
                "count": data.get("count", 0),
                "results": data.get("results", [])
            })
            
        except requests.exceptions.RequestException as e:
            error_msg = f"FastAPI service error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    error_msg = f"FastAPI error: {error_detail}"
                except:
                    error_msg = f"FastAPI error: {e.response.text}"
            return JsonResponse({"error": error_msg}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


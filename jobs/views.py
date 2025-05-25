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
from user.helpers import user_collection, jobs_collection
from wuzzuf.queue import send_to_queue
import time
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
def format_cv_url(cv_url):
    if cv_url.startswith("http"):
        return cv_url.split("/")[-1].replace(".pdf", "")
    return cv_url
def recommendation_vector_search(embedding, page, page_size,match_conditions):
    skip = (page - 1) * page_size
    
    regex = []
    if match_conditions.get("title", None):
        title = match_conditions.pop("title", None)
        regex.append({"title": title})
    if match_conditions.get("company_name", None):
        company_name = match_conditions.pop("company_name", None)
        regex.append({'company_name':company_name})
        
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector",
                "path": "combined_embedding",
                "queryVector": embedding,
                "numCandidates": 500,
                "limit": 100,
                "metric": "cosine",
                "filter": match_conditions
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "title": 1,
                'company_name': 1,
                "company_logo": 1,
                "experince": 1,
                "type_of_job": 1,
                'location': 1,
                'attend': 1,
                "description": 1,
                'created_at': 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        },
        {"$skip": skip},
        {"$limit": page_size}
    ]

    if regex:
        print(regex)
        pipeline.insert(1, {"$match": {"$and": regex}})

    results = list(jobs_collection.aggregate(pipeline))

    return results

def get_recommendationsView(request, user_id):
    try:
        user_id = int(user_id)
        user = User.objects.get(id=user_id)
        cv_url = user.cv
        
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)
        if not cv_url:
            return JsonResponse({"error": "User has no CV uploaded"}, status=400)

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 5))
        
        if page < 1 or page_size < 1:
            return JsonResponse({"error": "Page numbers must be 1 or higher"}, status=400)
        if page*page_size > 100:
            return JsonResponse({"error": "Max recommendations is 100"}, status=400)

        title = request.GET.get('title', '')
        experience = request.GET.get('experince', '')
        company_name = request.GET.get('company_name', '')
        location = request.GET.get('location', '')
        type_of_job = request.GET.get('type_of_job', '')
        attend = request.GET.get('attend', '')
        specialization = request.GET.get('specialization', '')

        match_conditions = {"status": "1"}
        if title:
            match_conditions["title"] = {"$regex": title, "$options": "i"}
        if company_name:
            match_conditions["company_name"] = {"$regex": company_name, "$options": "i"}
        if experience:
            match_conditions["experince"] = {"$in": experience.split(",")}
        if location:
            match_conditions["location"] = {"$in": location.split(",")}
        if type_of_job:
            match_conditions["type_of_job"] = {"$in": type_of_job.split(",")}
        if attend:
            match_conditions["attend"] = {"$in": attend.split(",")}
        if specialization:
            match_conditions["specialization"] = {"$in": specialization.split(",")}
            
        page_count = jobs_collection.count_documents(match_conditions)

        if page_count == 0:
            return JsonResponse({"error": "No jobs found"}, status=404)
        if page - 1 > page_count / page_size:
            return JsonResponse({"error": "Page number exceeds available pages"}, status=400)
        
        cv = True
        tries = 0
        while cv and tries < 5:
            user_data = user_collection.find_one({"user_id": user_id})
            print( format_cv_url(user_data.get("cv_url")), format_cv_url(getattr(cv_url, "url", "")))
            if user_data and user_data.get("embedding") and format_cv_url(user_data.get("cv_url")) == format_cv_url(getattr(cv_url, "url", "")):
                print("Using stored embedding (CV unchanged)")
                embedding = user_data["embedding"]
                cv = False
            else:
                print("Generating new embedding (CV changed)")
                fastapi_url = f"{FASTAPI_URL}/user_embedding/?user_id={user_id}&cv_url={cv_url}"
                # if(tries == 0): 
                #     send_to_queue('user_queue', "get", f"user_embedding/?user_id={user_id}&cv_url={cv_url}", {'user_id': user_id, "cv_url": cv_url.url})
                # time.sleep(4)

                # print (fastapi_url)
                try: 
                    response = requests.get(fastapi_url)
                    response.raise_for_status()
                    data = response.json()
                    
                    embedding = data.get("embedding")
                    
                    cv = False
                except requests.exceptions.RequestException as e:
                    error_msg = f"FastAPI service error: {str(e)}"
                    if hasattr(e, 'response') and e.response is not None:
                        error_msg = f"FastAPI error: {e.response.json().get('detail', e.response.text)}"
                    return JsonResponse({"error": error_msg}, status=500)
            # tries += 1
        
        recommendations = recommendation_vector_search(embedding, page, page_size, match_conditions)
        
        return JsonResponse({
            "page": page,
            "page_size": page_size,
            "total_results": page_count if page_count < 100 else 100,
            "recommendations": recommendations
        })
            
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

# def ats_match(request, user_id, job_id):
#     print("user_id", user_id)
#     print("job_id", job_id)
#     try:
#         user = User.objects.get(id=user_id)
#         print("user", user)
#     except User.DoesNotExist:
#         return JsonResponse({"error": "User not found"}, status=404)

#     try:
#         job = Job.objects.get(id=job_id)
#         print("job", job)
#     except Job.DoesNotExist:
#         return JsonResponse({"error": "Job not found"}, status=404)

#     if not user.cv:
#             # 3ayza  haga ttla3 f el front msg en el cv not found => ta2reban kda    
#            return JsonResponse({"error": "User CV not found", "message": "Please upload a CV before applying."}, status=400)

#     fastapi_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
#     print("fastapi_url", fastapi_url)

#     cv_url = str(user.cv) if user.cv else None
#     print("cv_url", cv_url)
   
#     payload = {
#         "cv_url": cv_url,
#         "job_id": job.id,
#         # "job_title": job.title,
#         # "job_description": job.description
#     }
#     print("payload", payload)

#     try:
#         response = requests.post(fastapi_url, json=payload, timeout=30)

#         print("response", response)
#         response_data = response.json()
#         print("response_data", response_data)
#         if not isinstance(response_data, dict):
#             return JsonResponse({"error": "Unexpected response format from FastAPI"}, status=500)

#         return JsonResponse(response_data, status=200)

#     except requests.exceptions.RequestException as e:
#         return JsonResponse({"error": "FastAPI request failed", "details": str(e)}, status=500)
def get_talentsView(request, job_id):
    try:
        if not job_id:
            return JsonResponse({"error": "Job ID is required"}, status=400)
            
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 5))
        seniority = request.GET.get('seniority', '')
        # print(page)
        # print(page_size)
        # print(seniority)

        if page < 1 or page_size < 1:
            return JsonResponse({"error": "Page numbers must be 1 or higher"}, status=400)

        page_count= user_collection.count_documents({'embedding': {'$exists': True}})

        if page_count == 0:
            return JsonResponse({"error": "No users found"}, status=404)
        if page*page_size > 100:
            return JsonResponse({"error": "Max recommendations is 100"}, status=400)
        if page - 1 > page_count / page_size:
            return JsonResponse({"error": "Page number exceeds available pages"}, status=400)

        job = jobs_collection.find_one({"id": job_id})

        if not job:
            return JsonResponse({"error": "Job not found"}, status=404)

        combined_embedding = job["combined_embedding"]

        filters = {}
        seniority = request.GET.get('seniority', '')
        if seniority:
            filters["seniority"] = {"$in": seniority.split(",")}
        if not combined_embedding:
            return JsonResponse({"error": "Combined embedding not found for the job"}, status=400)

        # Get top talents
        skip = (page - 1) * page_size
        vector_search = [
            {
                "$vectorSearch": {
                    "index": "default",
                    "queryVector": job["combined_embedding"],
                    "path": "embedding",
                    "numCandidates": 1000,
                    "limit": 100,
                    "metric": "cosine",
                    "filter": filters
                }
            },
            {
                 "$project": {
                    "_id": 0,
                    "id": '$user_id',
                    "ats_res": { "$meta": "vectorSearchScore" },
                    "name": 1,
                    "email": 1,
                    "seniority": 1
                 }
            },
            {"$skip": skip},  # Skip previous pages
            {"$limit": page_size}  #  Limit results per page
        ]

        # if seniority:
        #     vector_search.insert(0, {"$match": {"seniority": seniority}})

        results = list(user_collection.aggregate(vector_search))

        if not results or len(results) == 0:
            return JsonResponse({"error": "No matching talents found"}, status=404)
        # print(results)
        if filters and "seniority" in filters:
            page_count = user_collection.count_documents({'embedding': {'$exists': True}, 'seniority': {'$in': filters['seniority']['$in']}})
        return JsonResponse({
            "count": page_count if page_count < 100 else 100,
            "results": results
        })
    except Exception as e:
        print(f"An error occurred while retrieving the job: {e}")
        return JsonResponse({"error": "An error occurred while retrieving the talents"}, status=500)
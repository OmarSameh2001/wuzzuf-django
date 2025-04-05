from .models import Job
from .serializers import JobsSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import requests
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import JobFilter
from rest_framework import serializers
from questions.models import Question
from user.models import Company



FASTAPI_URL = "http://127.0.0.1:8001/jobs"
class JobPagination(PageNumberPagination):
     page_size = 5  # Adjust as needed
     page_size_query_param = 'page_size'
     max_page_size = 100


@method_decorator(csrf_exempt, name='dispatch')
class JobsViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter
    pagination_class = JobPagination
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        try:
          questions_data = request.data.pop('questions', [])
          company = Company.objects.get(id=request.data['company'])
          request.data['company'] = company
          
          for question_data in questions_data:
              Question.objects.create(job=job, **question_data)
          
          serializer = self.get_serializer(data=request.data)
          
          if serializer.is_valid():
            job_instance = serializer.save()
            
            fastapi_data = {
                "id": job_instance.id,
                "title": job_instance.title,
                "description": job_instance.description,
                "location": job_instance.location,
                "status": job_instance.status,
                "type_of_job": job_instance.type_of_job,
                "experince": job_instance.experince,
                "company": job_instance.company.id,
                "company_name": job_instance.company.name,
                "company_logo": self.get_serializer_context()['request'].build_absolute_uri(
                    job_instance.company.img.url
                ) if job_instance.company.img else "None",
            }

            print("company_instance", job_instance.company)
            print("fastapi_data", fastapi_data)
            
            try:
                response = requests.post(FASTAPI_URL, json=fastapi_data)
                response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                
                fastapi_response = response.json()
                print("fastapi_response", fastapi_response)
                
                return Response({"django_job": serializer.data, "fastapi_job": fastapi_response}, status=201)
            
            except requests.exceptions.RequestException as e:
                print("FastAPI request error:", e)
            
            return JsonResponse({"django_job": self.get_serializer(job).data, "fastapi_job": 'failed'}, status=201)
        
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while creating the job: {e}")

    # def create(self, request, *args, **kwargs):

    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         job_instance = serializer.save() 
            
    #         fastapi_data = {
    #             "id": job_instance.id,
    #             "title": job_instance.title,
    #             "description": job_instance.description,
               
    #         }
    #         print("fastaopi data ",fastapi_data)
    #         try:
    #             response = requests.post(FASTAPI_URL, json=fastapi_data)
    #             response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                
    #             fastapi_response = response.json()
    #             print("fastapi_response",fastapi_response)
    #             return Response({"django_job": serializer.data, "fastapi_job": fastapi_response}, status=201)
    #         except requests.exceptions.RequestException as e:
    #             return Response({"error": f"Failed to sync with FastAPI: {str(e)}"}, status=500)
        
    #     return Response(serializer.errors, status=400)
    

    def update(self, request, pk=None, partial=False):
        try:
         job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
         return Response({"error": "Job not found in django "}, status=404)

        serializer = JobsSerializer(job, data=request.data, partial=partial)
     
        if serializer.is_valid():
          updated_job = serializer.save()
        
        # Sync with FastAPI
          fastapi_data = {
            "id": updated_job.id,
            "title": updated_job.title,
            "description": updated_job.description,
            "location": updated_job.location,
            "status": updated_job.status,
            "type_of_job": updated_job.type_of_job,
            "experince": updated_job.experince, 
            "company": updated_job.company.id,
            "company_name": updated_job.company.name,
            "company_logo": self.get_serializer_context()['request'].build_absolute_uri(
                updated_job.company.img.url
            ) if updated_job.company.img else None,
          }
          try:
            fastapi_response = requests.put(f"{FASTAPI_URL}/{pk}", json=fastapi_data)
            fastapi_response.raise_for_status()
          except requests.exceptions.RequestException as e:
            return Response({"error": f"Failed to sync update with FastAPI: {e}"}, status=500)

          return Response(serializer.data)

        return Response(serializer.errors, status=400)


    def destroy(self, request, pk=None):
      try:
        job = Job.objects.get(pk=pk)
      except Job.DoesNotExist:
        return Response({"error": "Job not found django "}, status=404)

      job.delete()

       # Sync delete with FastAPI
      try:
         fastapi_response = requests.delete(f"{FASTAPI_URL}/{pk}")
         fastapi_response.raise_for_status()
      except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to sync delete with FastAPI: {e}"}, status=500)

      return Response(status=204)

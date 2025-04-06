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
    def create(self, request, *args, **kwargs):
        try:
            print("validated_data", request.data)
            validated_data = request.data
            questions_data = validated_data.pop('questions', [])  # Extract questions
            company = Company.objects.get(id=validated_data['company'])
            validated_data['company'] = company
            
            job = Job.objects.create(**validated_data)

            for question_data in questions_data:
                Question.objects.create(job=job, **question_data)  # Link each question to the job

            fastapi_data = {
                "id": job.id,
                "title": job.title,
                "description": job.description,
               
            }
            print("fastaopi data ",fastapi_data)
            try:
                response = requests.post(FASTAPI_URL, json=fastapi_data)
                response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                
                fastapi_response = response.json()
                print("fastapi_response",fastapi_response)
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
         print("job", job)
        except Job.DoesNotExist:
         return Response({"error": "Job not found in django "}, status=404)

        
        questions_data = request.data.pop('questions', [])
        serializer = JobsSerializer(job, data=request.data, partial=partial)
        if serializer.is_valid():
          print("validated_data")

        # print("instance", validated_data)
        # print("questions data", questions_data)
        # Delete existing questions and replace them with new ones
        Question.objects.filter(job=job).delete()
        for question_data in questions_data:
            print("question data", question_data, job)
            question_data.pop('job', None)
            Question.objects.create(job=job, **question_data)

        # Sync with FastAPI
        fastapi_data = {
          "id": job.id,
          "title": job.title,
          "description": job.description,
        }
        try:
          fastapi_response = requests.put(f"{FASTAPI_URL}/{pk}", json=fastapi_data)
          fastapi_response.raise_for_status()
          return Response({"django_job": serializer.data, "fastapi_job": fastapi_response.json()}, status=200)
        except requests.exceptions.RequestException as e:
          JsonResponse({"django_job": self.get_serializer(job).data, "fastapi_job": 'failed'}, status=200)

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

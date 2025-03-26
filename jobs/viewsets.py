from .models import Job
from .serializers import JobsSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import requests

FASTAPI_URL = "http://127.0.0.1:8001/jobs"
@method_decorator(csrf_exempt, name='dispatch')
class JobsViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobsSerializer
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            job_instance = serializer.save() 
            
            fastapi_data = {
                "id": job_instance.id,
                "title": job_instance.title,
                "description": job_instance.description,
               
            }
            print("fastaopi data ",fastapi_data)
            try:
                response = requests.post(FASTAPI_URL, json=fastapi_data)
                response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                
                fastapi_response = response.json()
                print("fastapi_response",fastapi_response)
                return Response({"django_job": serializer.data, "fastapi_job": fastapi_response}, status=201)
            except requests.exceptions.RequestException as e:
                return Response({"error": f"Failed to sync with FastAPI: {str(e)}"}, status=500)
        
        return Response(serializer.errors, status=400)
    
    
    
    def update(self, request, pk=None):
        job = Job.objects.get(pk=pk)
        serializer = JobsSerializer(job, data=request.data)
    
        if serializer.is_valid():
            print(serializer.validated_data)
            updated_job = serializer.save()
            

            fastapi_data = {
                "id":updated_job.id,
                "title":updated_job.title,
                "description":updated_job.description,
            }

            try:
                fastapi_response = requests.put(f"{FASTAPI_URL}/{pk}", json=fastapi_data)
                fastapi_response.raise_for_status()
                print(fastapi_response)
            except requests.exceptions.RequestException as e:
                return JsonResponse({"error": f"Failed to sync update with FastAPI: {e}"}, status=500)

            return Response(serializer.data)
    
        return Response(serializer.errors, status=400)

    def destroy (self, request, pk=None):
        try:
            job = Job.objects.get(pk=pk)
            job.delete()

            try:
                fastapi_response = requests.delete(f"{FASTAPI_URL}/{pk}")
                fastapi_response.raise_for_status()
                print(fastapi_response)
            except requests.exceptions.RequestException as e:
                return JsonResponse({"error": f"Failed to sync delete with FastAPI: {e}"}, status=500)

            return Response(status=204)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


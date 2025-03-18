from django.shortcuts import render
from .models import Jobs
from rest_framework import viewsets
from .serializers import JobsSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view

# from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
# Create your views here.

# class JobsViewSet(viewsets.ModelViewSet):
#     queryset = Jobs.objects.all()
#     serializer_class = JobsSerializer
#     #shofy ll filter w el search 
    






# @api_view(['GET'])
# def job_list(request):
#     jobs = Jobs.objects.all()
#     serializer = JobsSerializer(jobs, many=True)
#     return Response(serializer.data)
#    # return Response({"message": "This is the jobs list page."})

# @api_view(['GET'])
# def job_list(request):
#     jobs = Jobs.objects.all()
#     serializer = JobsSerializer(jobs, many=True)
#     return Response(serializer.data)

# @api_view(['GET'])
# def job_details (request , pK):
#     job =get_object_or_404(Jobs,pk=pK)
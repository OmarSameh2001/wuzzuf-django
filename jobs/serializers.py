from rest_framework.serializers import ModelSerializer
from .models import Job

class JobsSerializer(ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
    extra_kwargs = {
        'title': {'required': True},
        'description': {'required': True},
        'keywords': {'required': True},
        'experince': {'required': True},
        'status': {'required': True},
        'type_of_job': {'required': True},
    }   
    
    
    
        
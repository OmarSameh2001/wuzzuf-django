from rest_framework import serializers
from .models import Application
from jobs.models import Job
from jobs.serializers import JobsSerializer
from answers.models import Answer
from answers.serializers import AnswerSerializer



class ApplicationSerializer(serializers.ModelSerializer):
    # job_id = serializers.ReadOnlyField(source='job.id')  # Include Job ID
    #job_title = serializers.ReadOnlyField(source='job.title')  # Include Job Name
    user_name = serializers.ReadOnlyField(source='user.username')  # Include User Name
    user_email = serializers.ReadOnlyField(source='user.email')  # User Email
    user_phone = serializers.ReadOnlyField(source='user.phone_number')  # User Phone Number
    # user_status = serializers.ReadOnlyField(source='user.status')  # User Status (if exists)
    answers = serializers.SerializerMethodField()  # Custom method for nested answers
    job_details = JobsSerializer(read_only=True, source='job')  # Include nested Job details
    # Status = serializers.ReadOnlyField(source='get_status_display')  # Include status display name
    hr_link = serializers.CharField(required=False, allow_null=True)
    hr_time = serializers.DateTimeField(required=False, allow_null=True)
    interview_link = serializers.CharField(required=False, allow_null=True)
    interview_time = serializers.DateTimeField(required=False, allow_null=True)
    class Meta:
        model = Application
        fields = [
            'id','user', 'user_name', 'job', 'job_details', 'status', 'user_email','user_phone',
            'ats_res', 'screening_res', 'assessment_link', 'assessment_res', 
            'interview_link', 'interview_time', 
            'hr_link', 'hr_time', 'offer_time', 'offer_link', 'answers','fail','created_at', 'updated_at', 'salary', 'insurance', 'termination'
        ]

    def get_answers(self, obj):
        answers = Answer.objects.filter(application=obj)
        return AnswerSerializer(answers, many=True).data

    def create(self, validated_data):
        # Never have same application with user id and job id same
        if Application.objects.filter(user=validated_data['user'], job=validated_data['job']).exists():
            raise serializers.ValidationError("Application with this user and job already exists.")
        if validated_data['job'].status != "1":
            raise serializers.ValidationError("Job is not open for applications.")
        if validated_data['user'].cv is None:
            raise serializers.ValidationError("User CV is required.")
        # Create a new application with the given data
        return Application.objects.create(**validated_data)
    
    
    

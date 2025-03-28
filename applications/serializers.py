from rest_framework import serializers
from .models import Application
from jobs.models import Job
from jobs.serializers import JobsSerializer
from answers.models import Answer
from answers.serializers import AnswerSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    # job_id = serializers.ReadOnlyField(source='job.id')  # Include Job ID
    # job_title = serializers.ReadOnlyField(source='job.title')  # Include Job Name
    user_name = serializers.ReadOnlyField(source='user.username')  # Include User Name
    answers = serializers.SerializerMethodField()  # Custom method for nested answers
    job_details = JobsSerializer(read_only=True, source='job')  # Include nested Job details

    class Meta:
        model = Application
        fields = [
            'id','user', 'user_name', 'job', 'job_details', 'status', 
            'ats_res', 'screening_res', 'assessment_link', 'assessment_res', 
            'interview_link', 'interview_time', 'interview_options_time', 
            'hr_link', 'hr_time', 'hr_time_options', 'answers'
        ]

    def get_answers(self, obj):
        answers = Answer.objects.filter(application=obj)
        return AnswerSerializer(answers, many=True).data

    def create(self, validated_data):
        # Never have same application with user id and job id same
        if Application.objects.filter(user=validated_data['user'], job=validated_data['job']).exists():
            raise serializers.ValidationError("Application with this user and job already exists.")
        # Create a new application with the given data
        return Application.objects.create(**validated_data)


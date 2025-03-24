from rest_framework import serializers
from .models import Application
from jobs.models import Job
from answers.models import Answer
from answers.serializers import AnswerSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    # job_id = serializers.ReadOnlyField(source='job.id')  # Include Job ID
    job_title = serializers.ReadOnlyField(source='job.title')  # Include Job Name
    user_id = serializers.ReadOnlyField(source='user.id')  # Include User ID
    user_name = serializers.ReadOnlyField(source='user.username')  # Include User Name
    answers = serializers.SerializerMethodField()  # Custom method for nested answers

    class Meta:
        model = Application
        fields = [
            'id', 'user_id', 'user_name', 'job', 'job_title', 'status', 
            'ats_res', 'screening_res', 'assessment_link', 'assessment_res', 
            'interview_link', 'interview_time', 'interview_options_time', 
            'hr_link', 'hr_time', 'hr_time_options', 'answers'
        ]

    def get_answers(self, obj):
        answers = Answer.objects.filter(application=obj)
        return AnswerSerializer(answers, many=True).data
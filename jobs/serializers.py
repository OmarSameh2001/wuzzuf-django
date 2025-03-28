from rest_framework import serializers
from .models import Job
from questions.serializers import QuestionSerializer
from questions.models import Question
from user.serializers import CompanyProfileSerializer

class JobsSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()  # Allow handling multiple questions
    company_name = serializers.ReadOnlyField(source='company.name')
    company_logo = serializers.ReadOnlyField(source='company.img')

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'company','company_name', 'company_logo', 'experince', 'type_of_job', 'location', 'keywords', 'status', 'questions', 'created_at']

    def get_questions(self, obj):
        return QuestionSerializer(Question.objects.filter(job=obj), many=True).data



    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])  # Extract questions
        job = Job.objects.create(**validated_data)

        for question_data in questions_data:
            Question.objects.create(job=job, **question_data)  # Link each question to the job

        return job

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # Optional: Delete existing questions and replace them with new ones
        instance.questions.all().delete()
        for question_data in questions_data:
            Question.objects.create(job=instance, **question_data)

        return instance

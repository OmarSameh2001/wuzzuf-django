from rest_framework import serializers
from .models import Job
from questions.serializers import QuestionSerializer
from questions.models import Question

class JobsSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()  # Allow handling multiple questions

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'experince', 'type_of_job', 'location', 'keywords', 'status', 'questions', 'created_at']

    def get_questions(self, obj):
        # Retrieve questions only if it's a single object detail request
        request = self.context.get('request')
        if request and request.parser_context.get('kwargs', {}).get('pk'):  
            questions = Question.objects.filter(job=obj)
            return QuestionSerializer(questions, many=True).data
        return []  # Return empty list for list views

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
        
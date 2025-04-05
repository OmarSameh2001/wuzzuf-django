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
     
        fields = ['id', 'title', 'description', 'company','company_name', 'company_logo', 'experince', 'type_of_job', 'location',  'status', 'created_at', 'questions']# 'questions',

    def get_questions(self, obj):
        return QuestionSerializer(Question.objects.filter(job=obj), many=True).data

    def get_company_logo(self, obj):
        if obj.company.img:
            print("company logo",obj.company.img.url)
            from cloudinary import CloudinaryImage
            img = CloudinaryImage(str(obj.company.img))
            return img.build_url()
            # return obj.company.img.url
        #self.context['request'].build_absolute_uri(obj.company.img.url)
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['company_logo'] = self.get_company_logo(instance)
        return representation
    
    
    
    
    def create(self, validated_data):
        try:
            questions_data = validated_data.pop('questions', [])  # Extract questions
            job = Job.objects.create(**validated_data)

            for question_data in questions_data:
                Question.objects.create(job=job, **question_data)  # Link each question to the job

            return job
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while creating the job: {e}")

    def update(self, instance, validated_data):
        # questions_data = validated_data.pop('questions', [])
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        instance.experince = validated_data.get('experince', instance.experince)
        instance.type_of_job = validated_data.get('type_of_job', instance.type_of_job)
        instance.location = validated_data.get('location', instance.location)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        # Optional: Delete existing questions and replace them with new ones
        # instance.questions.all().delete()
        # for question_data in questions_data:
        #     Question.objects.create(job=instance, **question_data)

        return instance

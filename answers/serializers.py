from rest_framework.serializers import ModelSerializer
from .models import Answer


class AnswerSerializer(ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"
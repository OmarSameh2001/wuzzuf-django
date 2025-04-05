from rest_framework.serializers import ModelSerializer
from .models import Answer
from rest_framework import serializers

class AnswerSerializer(ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"

    def create(self, validated_data):
        # Check if duplicate answer exists for the same application and question
        if Answer.objects.filter(application=validated_data['application'], question=validated_data['question']).exists():
            raise serializers.ValidationError("Duplicate answer for this application and question already exists.")

        return Answer.objects.create(**validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        if request is None or not request.user.is_staff:
            representation = super().to_representation(instance)
            representation.pop('result', None)
            return representation
        return super().to_representation(instance)
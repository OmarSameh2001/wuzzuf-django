from rest_framework.serializers import ModelSerializer
from .models import Question


class QuestionSerializer(ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        if request is None or not request.user.is_staff:
            representation = super().to_representation(instance)
            representation.pop('answer_q', None)
            return representation
        return super().to_representation(instance)

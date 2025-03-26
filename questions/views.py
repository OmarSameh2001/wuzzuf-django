from rest_framework import viewsets
from .serializers import QuestionSerializer
from .models import Question

# Create your views here.


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

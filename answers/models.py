from django.db import models
from applications.models import Application
from questions.models import Question

# Create your models here.
class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    result = models.CharField(max_length=255, blank=True, null=True)  # e.g., Correct, Incorrect, Passed

    def __str__(self):
        return f"{self.user_job.user.name} - {self.question.text[:30]}..."
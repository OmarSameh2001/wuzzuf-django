from django.db import models

# Create your models here.

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=200)
    answer_q = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=50, choices=[('boolean', 'boolean'), ('text', 'text')], default='boolean')

    def __str__(self):
        return self.text
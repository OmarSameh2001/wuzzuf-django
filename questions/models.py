from django.db import models

# Create your models here.


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    answer_q = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=50, choices=[('boolean', 'boolean'), ('multichoice', 'multichoice'), ('video', 'video')], default='boolean')
    choices = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=True)

    def __str__(self):
        return self.text

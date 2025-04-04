from django.db import models
from jobs.models import Job
from user.models import Jobseeker
# Create your models here.
class Application(models.Model):
     
    STATUS_CHOICES = [
        (2, "Application Accepted"),
        (3, "Technical Assessment"),
        (4, "Technical Interview"),
        (5, "HR Interview"),
        (6, "Offer Interview"),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Jobseeker, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='1')
    ats_res = models.TextField(blank=True, null=True)
    screening_res = models.TextField(blank=True, null=True)
    assessment_link = models.CharField(max_length=255, blank=True, null=True)
    assessment_res = models.TextField(blank=True, null=True)
    interview_link = models.CharField(max_length=255, blank=True, null=True)
    interview_time = models.DateTimeField(blank=True, null=True)
    # interview_options_time = models.JSONField(blank=True, null=True)  # Store multiple times as JSON
    hr_link = models.CharField(max_length=255, blank=True, null=True)
    hr_time = models.DateTimeField(blank=True, null=True)
    # hr_time_options = models.JSONField(blank=True, null=True)  # Store multiple HR times as JSON
    offer_time = models.DateTimeField(blank=True, null=True)
    offer_link = models.CharField(max_length=255, blank=True, null=True)
    fail = models.BooleanField(default=False)
    def __str__(self):
         return f"{self.user.username} - {self.job.title} - {self.status}"
        #return f"{self.job.title}"
from django.db import models
from user.models import User

# Create your models here.
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    experince = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    type_of_job = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True )
    company = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    limit_choices_to={'user_type': User.UserType.COMPANY},
    related_name='jobs',
    null=True,  
    blank=True  
    )
    def __str__(self):
        return self.title
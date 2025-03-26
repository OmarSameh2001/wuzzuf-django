from django.db import models


# Create your models here.
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    keywords = models.CharField(max_length=255)
    experince = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    type_of_job = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True )
    #na2es el company 
    #company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
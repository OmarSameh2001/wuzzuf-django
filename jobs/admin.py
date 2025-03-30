from django.contrib import admin
from .models import Job
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description', 'location', 'keywords', 'experince', 'status', 'type_of_job', 'created_at']
    list_filter = ['status', 'type_of_job']
    search_fields = ['title', 'description', 'keywords']

admin.site.register(Job, JobAdmin)

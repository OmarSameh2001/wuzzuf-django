from django.contrib import admin

# Register your models here.
from .models import Application

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'user', 'status')

admin.site.register(Application, ApplicationAdmin)


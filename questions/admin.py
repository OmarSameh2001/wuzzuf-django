from django.contrib import admin
from .models import Question

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'job', 'type', 'required')
    list_filter = ('job', 'type', 'required')
    search_fields = ('text',)

admin.site.register(Question, QuestionAdmin)
    # Register your models here.

from django.contrib import admin
from .models import Answer


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'question', 'answer_text', 'result')


    
# Register your models here.
admin.site.register(Answer, AnswerAdmin)
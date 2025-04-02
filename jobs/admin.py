from django.contrib import admin
from .models import Job
from user.models import Company
import requests
FASTAPI_URL = "http://127.0.0.1:8001/jobs"
class JobAdmin(admin.ModelAdmin):
    ordering = ['id']
    list_display = ['id', 'title', 'description','location',  'experince', 'status', 'type_of_job', 'created_at', 'company']
    fieldsets = (
        (None, {'fields': ('title', 'description', 'location', 'experince', 'status', 'type_of_job', 'company')}),
    )
    readonly_fields = ['created_at']  # Prevents modification
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'title', 'description', 'location', 'keywords', 'experince', 'status', 'type_of_job', 'company'
            )
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'company':
            kwargs['queryset'] = Company.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # Save job in Django

        # Sync with FastAPI
        fastapi_data = {
            "id": obj.id,
            "title": obj.title,
            "description": obj.description,
        }
        try:
            response = requests.post(FASTAPI_URL, json=fastapi_data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.message_user(request, f"Failed to sync with FastAPI: {e}", level='ERROR')

admin.site.register(Job, JobAdmin)


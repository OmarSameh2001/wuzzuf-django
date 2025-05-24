from django.contrib import admin
from .models import Job
from user.models import Company
import requests
import os
from dotenv import load_dotenv
from wuzzuf.queue import send_to_queue
load_dotenv()
from user.helpers import jobs_collection


FASTAPI_URL = os.environ.get("FAST_API")
class JobAdmin(admin.ModelAdmin):
    ordering = ['id']
    list_display = ['id', 'title', 'description','location',  'experince', 'status', 'type_of_job', 'created_at', 'company','attend', 'specialization']
    fieldsets = (
        (None, {'fields': ('title', 'description', 'location', 'experince', 'status', 'type_of_job', 'company', 'specialization', 'attend', 'created_at')}),
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
            "location": obj.location,
            "status": obj.status,
            "type_of_job": obj.type_of_job,
            "experince": obj.experince,
            "company": obj.company.id,
            "company_name": obj.company.name,
            "company_logo": request.build_absolute_uri(obj.company.img.url) if obj.company.img else None,

        }
        try:
            if change:
                # If the job is being updated
            #  response = requests.put(f"{FASTAPI_URL}/{obj.id}", json=fastapi_data)
                send_to_queue("job_queue", "put", f"jobs/{obj.id}", fastapi_data)
            else:
            # If the job is being created
            #  response = requests.post(FASTAPI_URL + "/jobs", json=fastapi_data)
                send_to_queue("job_queue", "post", f"jobs", fastapi_data)

            # response.raise_for_status()

        except Exception as e:
          self.message_user(request, f"Failed to sync with FastAPI: {e}", level='ERROR')
          
          
    def delete_model(self, request, obj):
        try:
            jobs_collection.delete_one({"id": obj.id})
        except requests.exceptions.RequestException as e:
            self.message_user(request, f"Failed to delete from FastAPI: {e}", level='ERROR')

        super().delete_model(request, obj)      

admin.site.register(Job, JobAdmin)


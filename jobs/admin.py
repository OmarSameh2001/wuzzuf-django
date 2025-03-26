from django.contrib import admin
from .models import Job

class JobAdmin(admin.ModelAdmin):
    ordering = ['id']
    list_display = ['id', 'title', 'description', 'location', 'keywords', 'experince', 'status', 'type_of_job', 'created_at']
    fieldsets = (
        (None, {'fields': ('title', 'description', 'location', 'keywords', 'experince', 'status', 'type_of_job')}),
    )
    readonly_fields = ['created_at']  # Prevents modification
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'title', 'description', 'location', 'keywords', 'experince', 'status', 'type_of_job'
            )
        }),
    )

admin.site.register(Job, JobAdmin)


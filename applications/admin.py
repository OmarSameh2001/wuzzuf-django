from django.contrib import admin

# Register your models here.
from .models import Application
from applications.views import perform_create_for_admin
class ApplicationAdmin(admin.ModelAdmin):

    list_display = ('id', 'job', 'user', 'status')
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            result = perform_create_for_admin(obj)
            self.message_user(request, f"ATS score processed successfully.")
        except Exception as e:
            self.message_user(request, f"Error during ATS processing: {e}", level='ERROR')


admin.site.register(Application, ApplicationAdmin)


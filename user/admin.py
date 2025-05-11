from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from user.models import User, Jobseeker, Company, Itian
import csv
from io import StringIO
import pandas as pd
from django.core.validators import EmailValidator
from .models import validate_egyptian_national_id
from .views import user_collection
from .models import Track, Branch  

class CustomUserAdmin(UserAdmin):
    ordering = ["id"]
    list_filter = ["user_type"]
    list_display = [
        "id",
        "email",
        "username",
        "name",
        "phone_number",
        "user_type",
        "is_active",
        "is_staff",
    ]
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            _( "Personal Info" ),
            {
                "fields": (
                    "name",
                    "phone_number",
                    "location",
                    "img",
                    
                )
            },
        ),
        (
            _( "Permissions" ),
            {"fields": ("is_active", "is_staff", "is_superuser", "user_type")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")} ),
    )
    readonly_fields = ["last_login", "date_joined"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "name",
                    "phone_number",
                    "location",
                    "img",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "user_type",
                ),
            },
        ),
    )


# Register Track model
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Adjust these fields as needed
    search_fields = ('name',)  # Allow search by track name

# Register Branch model
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')  # Adjust these fields as needed
    search_fields = ('name', 'address')  # Allow search by branch name


@admin.register(Jobseeker)
class JobseekerAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "name", "dob", "education", "experience", "about","summary", "skills","cv", "img", "get_track", "get_branch", "iti_grad_year"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email", "username", "password", "name", "dob", "phone_number", "img", "skills","is_verified"
                )
            },
        ),
        ("Profile", {"fields": ("summary","about","education", "experience","cv","accounts","seniority","specialization")}),
        ("National ID Details", {"fields": ("national_id", "national_id_img")}),
    )
    readonly_fields = ["last_login"]

    def get_track(self, obj):
        if obj.track:
            return obj.track.name
        return "-"
    get_track.short_description = "Track"

    def get_branch(self, obj):
        if obj.branch:
            return obj.branch.name
        return "-"
    get_branch.short_description = "Branch"


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.user_type == User.UserType.JOBSEEKER and not change:    
            user_collection.insert_one({"user_id": obj.id, "email": obj.email, 'name': obj.name})

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "name", "est", "industry", "img"]
    fieldsets = (
        (
            None,
            {"fields": ("email", "username", "password", "name", "phone_number")},
        ),
        ("Company Details", {"fields": ("est", "industry", "img", "accounts","is_verified",)}),
    )
    readonly_fields = ["last_login"]

@admin.register(Itian)
class Itian(admin.ModelAdmin):
    list_display = ['id', 'email', 'national_id']
    fieldsets = (
        (
            None,
            {"fields": ('email', 'national_id')},
        ),
        ("Bulk Add by csv", {"fields": ('file',)}),
    )

    def save_model(self, request, obj, form, change):
        file = request.FILES.get('file', None)
        
        if file:
            # Handle file upload case
            file_name = file.name
            try:
                if file_name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file)
                elif file_name.endswith('.csv'):
                    try:
                        df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(file, encoding='ISO-8859-1', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            df = pd.read_csv(file, encoding='Windows-1252', on_bad_lines='skip')
                else:
                    self.message_user(request, 'Unsupported file format. Please upload a CSV or Excel file.', level='ERROR')
                    return

                if 'email' not in df.columns or 'national_id' not in df.columns:
                    self.message_user(request, 'File must contain "email" and "national_id" columns', level='ERROR')
                    return

                num = 0
                for index, row in df.iterrows():
                    email = row['email']
                    national_id = row['national_id']
                    try:
                        # Validate email format
                        EmailValidator()(email)
                        validate_egyptian_national_id(str(national_id))
                        if self.model.objects.filter(email=email, national_id=national_id).exists():
                            self.message_user(request, f"User {email} already exists.", level='WARNING')
                            continue
                        
                        self.model.objects.create(
                            email=email,
                            national_id=national_id,
                        )
                        num += 1
                        self.message_user(request, f"User {email} created successfully.")
                    except Exception as e:
                        self.message_user(request, f"Error creating user {email}: {e}", level='ERROR')
                        continue

                if num > 0:
                    self.message_user(request, f"Successfully created {num} users.")
                else:
                    self.message_user(request, "No new users created.")
                
                return  # ⚠️ Important: Return here to prevent default save

            except Exception as e:
                self.message_user(request, f"Error processing file: {e}", level='ERROR')
                return

        # Handle regular form submission (no file)
        super().save_model(request, obj, form, change)



# Register the models with the admin panel
admin.site.register(Track, TrackAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(User, CustomUserAdmin)
# admin.site.register(Jobseeker, JobseekerAdmin)
# admin.site.register(Company, CompanyAdmin)


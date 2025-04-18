from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from user.models import User, Jobseeker, Company


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

@admin.register(Jobseeker)
class JobseekerAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "name", "dob", "education", "experience", "skills","cv", "img" ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email", "username", "password", "name", 'about', "dob", "phone_number", "img", "skills"
                )
            },
        ),
        ("Profile", {"fields": ("education", "experience", "cv")}),
        ("National ID Details", {"fields": ("national_id", "national_id_img")}),
    )
    readonly_fields = ["last_login"]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "name", "est", "industry", "img"]
    fieldsets = (
        (
            None,
            {"fields": ("email", "username", "password", "name", "phone_number")},
        ),
        ("Company Details", {"fields": ("est", "industry", "img")}),
    )
    readonly_fields = ["last_login"]


admin.site.register(User, CustomUserAdmin)
# admin.site.register(Jobseeker, JobseekerAdmin)
# admin.site.register(Company, CompanyAdmin)


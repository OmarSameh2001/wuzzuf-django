from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from user.models import User, Jobseeker, Company


class CustomUserAdmin(UserAdmin):
    ordering = ["id"]
    list_filter = ["user_type"]
    list_display = [
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


class JobseekerAdmin(admin.ModelAdmin):
    list_display = ["email", "name", "dob", "education", "experience", "cv"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email", "username", "password", "name", "dob", "phone_number"
                )
            },
        ),
        (_("Profile"), {"fields": ("education", "experience", "cv", "keywords")} ),
        (_("National ID Details"), {"fields": ("national_id", "national_id_img")} ),
    )
    readonly_fields = ["last_login"]


class CompanyAdmin(admin.ModelAdmin):
    list_display = ["email", "name", "est", "industry"]
    fieldsets = (
        (
            None,
            {"fields": ("email", "username", "password", "name", "phone_number")},
        ),
        (_("Company Details"), {"fields": ("est", "industry")} ),
    )
    readonly_fields = ["last_login"]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Jobseeker, JobseekerAdmin)
admin.site.register(Company, CompanyAdmin)

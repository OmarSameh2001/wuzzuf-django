"""
django admin customization
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from . import models  
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html 

class UserAdmin(BaseUserAdmin):
    #define admin pages for users
    ordering = ['id']
    list_display = ['email', 'username', 'name', 'phone_number', 'is_company', 'is_active', 'is_staff']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal Info'), {
            'fields': (
                'name', 'dob', 'phone_number', 'location', 
                'education', 'experience', 'cv', 'img', 'keywords'
            )
        }),
        (_('National ID Details'), {
            'fields': ('national_id', 'national_id_img')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_company',
            )
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    readonly_fields = ['last_login']  # Prevents modification

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'name', 'dob', 'phone_number', 'location',
                'education', 'experience', 'cv', 'img', 'keywords',
                'national_id', 'national_id_img',
                'is_active', 'is_staff', 'is_superuser', 'is_company'
            )
        }),
    )

# Register your models here.
admin.site.register(models.User, UserAdmin)
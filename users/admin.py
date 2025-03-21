
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users import models
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin):
    #define admin pages for users
    ordering = ['id']
    list_display = ['email', 'name', 'username']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_company'
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
                'is_company'
            )
        }),
    )


# Register your models here.
admin.site.register(models.User, UserAdmin)

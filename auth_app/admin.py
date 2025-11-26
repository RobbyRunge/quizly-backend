from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Unregister the default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin interface with enhanced display and filters.
    """
    list_display = (
        'username',
        'email',
        'is_staff',
        'date_joined'
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'date_joined'
    )

    search_fields = (
        'username',
        'email',
    )

    ordering = ('-date_joined',)

    readonly_fields = ('date_joined',)

    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('email',)
        }),
        ('Permissions', {
            'fields': (
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('date_joined',)
        }),
    )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_agent',)}),
        (_('Important dates'), {'fields': ('create_time', 'update_time')}),
    )
    add_fieldsets = (None, {'fields': ('username', 'password', 'email', 'is_agent'),})
    list_display = ('username', 'email', 'is_active', 'is_agent', 'create_time', 'update_time')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    def delete_users(self, request, queryset):
        queryset.update(is_delete=True)

admin.site.register(User, UserAdmin)


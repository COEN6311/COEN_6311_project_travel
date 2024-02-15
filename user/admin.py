from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_agent')
    search_fields = ['username', 'email', 'is_active', 'is_agent']
    actions = ['deactivate_users', 'delete_users']

    def deactivate_users(self, request, queryset):
        '''Deactivate selected users.'''
        queryset.update(is_active=False)
    deactivate_users.short_description = 'Deactivate selected users'

    def delete_users(self, request, queryset):
        ''' Delete selected users.'''
        queryset.delete()
    delete_users.short_description = 'Delete selected users'
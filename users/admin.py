from django.contrib import admin

from core.admin import BaseModelAdmin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(BaseModelAdmin):
    list_display = ('user', 'goal', 'age', 'height', 'weight', 'is_active')
    list_filter = ('goal', 'is_active')
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user',)

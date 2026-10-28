from django.contrib import admin

from core.admin import BaseModelAdmin

from .models import DietPlan, Meal


@admin.register(DietPlan)
class DietPlanAdmin(BaseModelAdmin):
    list_display = ('name', 'user', 'calories', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'user__username')
    autocomplete_fields = ('user',)


@admin.register(Meal)
class MealAdmin(BaseModelAdmin):
    list_display = ('name', 'diet_plan', 'calories', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'diet_plan__name')
    autocomplete_fields = ('diet_plan',)

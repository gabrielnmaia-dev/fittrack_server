from django.contrib import admin

from core.admin import BaseModelAdmin

from .models import Exercise, Workout


@admin.register(Exercise)
class ExerciseAdmin(BaseModelAdmin):
    list_display = ('name', 'muscle_group', 'sets', 'reps', 'user', 'is_active')
    list_filter = ('muscle_group', 'is_active')
    search_fields = ('name', 'description', 'muscle_group')
    autocomplete_fields = ('user',)


@admin.register(Workout)
class WorkoutAdmin(BaseModelAdmin):
    list_display = ('name', 'user', 'level', 'duration', 'is_active', 'created_at')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'description', 'user__username')
    autocomplete_fields = ('user',)
    filter_horizontal = ('exercises',)

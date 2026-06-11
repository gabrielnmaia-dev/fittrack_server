from django.contrib import admin
from .models import DietPlan, Meal
# Register your models here.
admin.site.register(DietPlan)
admin.site.register(Meal)
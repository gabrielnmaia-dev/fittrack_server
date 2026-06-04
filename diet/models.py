from django.db import models

from core.models import BaseModel

# Create your models here.

class DietPlan(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    calories = models.PositiveIntegerField(help_text="Calorias diarias")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='diet_plans')
    
class Meal(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    calories = models.PositiveIntegerField(help_text="Calorias da refeicao")
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='meals')

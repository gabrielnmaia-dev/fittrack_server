from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel


class DietPlan(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    calories = models.PositiveIntegerField(
        help_text='Calorias diárias',
        validators=[MinValueValidator(1)],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diet_plans',
    )

    class Meta(BaseModel.Meta):
        ordering = ('-created_at', '-id')
        verbose_name = 'plano de dieta'
        verbose_name_plural = 'planos de dieta'

    def __str__(self):
        return self.name


class Meal(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    calories = models.PositiveIntegerField(
        help_text='Calorias da refeição',
        validators=[MinValueValidator(1)],
    )
    diet_plan = models.ForeignKey(
        DietPlan,
        on_delete=models.CASCADE,
        related_name='meals',
    )

    class Meta(BaseModel.Meta):
        ordering = ('created_at', 'id')
        verbose_name = 'refeição'
        verbose_name_plural = 'refeições'

    def __str__(self):
        return self.name

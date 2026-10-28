from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel


class UserProfile(BaseModel):
    """Extra fitness data attached to the authentication user."""

    GOAL_CHOICES = [
        ('lose_weight', 'Perder peso'),
        ('gain_muscle', 'Ganhar músculo'),
        ('maintain_weight', 'Manter peso'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
    )
    height = models.FloatField(
        help_text='Altura em centímetros',
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    weight = models.FloatField(
        help_text='Peso em quilogramas',
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES)

    class Meta(BaseModel.Meta):
        verbose_name = 'perfil de usuário'
        verbose_name_plural = 'perfis de usuário'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return self.user.username

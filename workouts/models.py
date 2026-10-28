from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel


class Exercise(BaseModel):
    """Exercise catalog entry.

    Exercises created by a user (``user`` set) are private to that user.
    Exercises without an owner (``user is None``) form the global catalog and
    are managed by the staff.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    sets = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    reps = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    muscle_group = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exercises',
        null=True,
        blank=True,
        help_text='Vazio para exercícios do catálogo global',
    )

    class Meta(BaseModel.Meta):
        ordering = ('name', 'id')
        verbose_name = 'exercício'
        verbose_name_plural = 'exercícios'

    def __str__(self):
        return self.name


class Workout(BaseModel):
    LEVEL_CHOICES = [
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.PositiveIntegerField(
        help_text='Duração em minutos',
        validators=[MinValueValidator(1)],
    )
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts',
    )
    exercises = models.ManyToManyField(
        Exercise,
        related_name='workouts',
        blank=True,
    )

    class Meta(BaseModel.Meta):
        ordering = ('-created_at', '-id')
        verbose_name = 'plano de treino'
        verbose_name_plural = 'planos de treino'

    def __str__(self):
        return self.name

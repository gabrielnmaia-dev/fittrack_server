from django.db import models

from core.models import BaseModel

# Create your models here.
class Exercise(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    muscle_group = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Workout(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duração em minutos")
    level = models.CharField(max_length=50, choices=[('beginner', 'Iniciante'), ('intermediate', 'Intermediario'), ('advanced', 'Avançado')])
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='workouts')
    exercises = models.ManyToManyField('Exercise', related_name='workouts', blank=True)
    
    def __str__(self):
        return self.name
from django.db import models
from core.models import BaseModel

# Create your models here.

class UserProfile(BaseModel):
    GOAL_CHOICES = [
        ('lose_weight', 'Perder peso'),
        ('gain_muscle', 'Ganhar músculo'),
        ('maintain_weight', 'Manter peso'),
    ]
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    height = models.FloatField()
    weight = models.FloatField()
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES)
    def __str__(self):
        return self.user.username
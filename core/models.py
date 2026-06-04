from django.db import models

# Create your models here.
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ActiveManager() #retorna apenas os objetos ativos
    all_objects = models.Manager() #retorna todos os objetos, inclusive os inativos
    
    def delete(self):
        self.is_active = False
        self.save()
        
    class Meta:
        abstract = True
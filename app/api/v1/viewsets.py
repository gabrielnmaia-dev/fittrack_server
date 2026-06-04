from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from diet.models import DietPlan, Meal
from workouts.models import Workout, Exercise
from users.models import UserProfile
from .serializers import UserProfileSerializer, DietPlanSerializer, MealSerializer, ExerciseSerializer, WorkoutSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
class DietPlanViewSet(viewsets.ModelViewSet):    
    queryset = DietPlan.objects.all()
    serializer_class = DietPlanSerializer
    permission_classes = [IsAuthenticated]
    
class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated]
    
class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    
class WorkoutViewSet(viewsets.ModelViewSet):        
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
    
    
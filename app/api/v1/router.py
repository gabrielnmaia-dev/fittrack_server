from rest_framework.routers import DefaultRouter

from .viewsets import (
    DietPlanViewSet,
    ExerciseViewSet,
    MealViewSet,
    UserViewSet,
    WorkoutViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workout-plans', WorkoutViewSet, basename='workout')
router.register(r'diet-plans', DietPlanViewSet, basename='dietplan')
router.register(r'meals', MealViewSet, basename='meal')

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter
from .viewsets import UserProfileViewSet, DietPlanViewSet, MealViewSet, ExerciseViewSet, WorkoutViewSet

router = DefaultRouter()
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'dietplans', DietPlanViewSet)
router.register(r'meals', MealViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'workouts', WorkoutViewSet)

urlpatterns = router.urls
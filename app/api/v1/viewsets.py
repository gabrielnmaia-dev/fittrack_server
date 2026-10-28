from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from diet.models import DietPlan, Meal
from workouts.models import Exercise, Workout

from .permissions import IsOwnerOrStaff
from .serializers import (
    DietPlanSerializer,
    ExerciseSerializer,
    MealSerializer,
    UserSerializer,
    WorkoutSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Public registration endpoint (POST /api/v1/auth/register/)."""

    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class UserViewSet(viewsets.ModelViewSet):
    """User management.

    ``POST /users/`` is public and is the registration endpoint. A regular
    user can only read/update their own record (see ``/users/me/``); staff can
    list and deactivate any user.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ('is_active',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering_fields = ('username', 'date_joined')
    ordering = ('-date_joined',)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(pk=user.pk)

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ('list', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        # Deactivate instead of deleting: keeps plans/history consistent.
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH',
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OwnedQuerysetMixin:
    """Restrict querysets to the authenticated user unless staff."""

    owner_filter = 'user'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(**{self.owner_filter: user})


class ExerciseViewSet(viewsets.ModelViewSet):
    """Exercise catalog.

    The global catalog (``user`` null) is visible to every authenticated user
    but only staff can change it. Users can create and manage their own
    exercises.
    """

    queryset = Exercise.objects.select_related('user')
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filterset_fields = ('muscle_group',)
    search_fields = ('name', 'description', 'muscle_group')
    ordering_fields = ('name', 'muscle_group', 'created_at')
    ordering = ('name',)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(Q(user__isnull=True) | Q(user=user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Workout.objects.select_related('user').prefetch_related('exercises')
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('level', 'user')
    search_fields = ('name', 'description')
    ordering_fields = ('name', 'duration', 'level', 'created_at')
    ordering = ('-created_at',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DietPlanViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        DietPlan.objects.select_related('user')
        .prefetch_related('meals')
    )
    serializer_class = DietPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('user',)
    search_fields = ('name', 'description')
    ordering_fields = ('name', 'calories', 'created_at')
    ordering = ('-created_at',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MealViewSet(viewsets.ModelViewSet):
    queryset = (
        Meal.objects.select_related('diet_plan', 'diet_plan__user')
    )
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('diet_plan',)
    search_fields = ('name', 'description')
    ordering_fields = ('name', 'calories', 'created_at')
    ordering = ('created_at',)

    def get_queryset(self):
        queryset = super().get_queryset().filter(diet_plan__is_active=True)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(diet_plan__user=user)

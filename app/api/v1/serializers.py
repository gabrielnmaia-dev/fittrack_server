from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from diet.models import DietPlan, Meal
from users.models import UserProfile
from workouts.models import Exercise, Workout

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'age', 'height', 'weight', 'goal')
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
    """Serializer used for registration and for the authenticated user."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
    )
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'profile',
            'is_staff',
            'date_joined',
        )
        read_only_fields = ('id', 'is_staff', 'date_joined')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.fields['password'].required = True
        if self.partial and 'profile' in self.fields:
            # Nested partial updates (e.g. PATCH /users/me/ {profile: {weight}}).
            self.fields['profile'].partial = True

    def validate_password(self, value):
        user = self.instance or User(username=self.initial_data.get('username', ''))
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password')
        with transaction.atomic():
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            if profile_data:
                UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            if password:
                instance.set_password(password)
            instance.save()

            if profile_data is not None:
                UserProfile.all_objects.update_or_create(
                    user=instance,
                    defaults={**profile_data, 'is_active': True},
                )
        return instance


class ExerciseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    is_global = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = (
            'id',
            'name',
            'description',
            'sets',
            'reps',
            'muscle_group',
            'user',
            'is_global',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_is_global(self, obj) -> bool:
        return obj.user_id is None


class WorkoutSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise_details = ExerciseSerializer(source='exercises', many=True, read_only=True)

    class Meta:
        model = Workout
        fields = (
            'id',
            'name',
            'description',
            'duration',
            'level',
            'user',
            'exercises',
            'exercise_details',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
        extra_kwargs = {
            'exercises': {'required': False},
        }

    def validate_exercises(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or user.is_staff:
            return value

        invalid = [
            exercise
            for exercise in value
            if exercise.user_id not in (None, user.id)
        ]
        if invalid:
            raise serializers.ValidationError(
                'Você só pode usar exercícios do catálogo global ou criados por você.'
            )
        return value


class MealSerializer(serializers.ModelSerializer):
    diet_plan = serializers.PrimaryKeyRelatedField(queryset=DietPlan.objects.all())

    class Meta:
        model = Meal
        fields = (
            'id',
            'name',
            'description',
            'calories',
            'diet_plan',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_diet_plan(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or user.is_staff:
            return value
        if value.user_id != user.id:
            raise serializers.ValidationError(
                'Você só pode adicionar refeições aos seus próprios planos de dieta.'
            )
        return value


class DietPlanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    meals = MealSerializer(many=True, read_only=True)

    class Meta:
        model = DietPlan
        fields = (
            'id',
            'name',
            'description',
            'calories',
            'user',
            'meals',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

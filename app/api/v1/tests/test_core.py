from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import authenticate, create_user


class HealthTests(APITestCase):
    def test_health_endpoint_is_public(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'ok'})

    def test_health_alias_under_api_prefix(self):
        response = self.client.get('/api/v1/health/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SchemaTests(APITestCase):
    def setUp(self):
        self.user = create_user('alice')
        self.staff = create_user('admin', is_staff=True)

    def test_openapi_schema_is_generated(self):
        authenticate(self.client, self.staff)

        response = self.client.get(reverse('schema'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode()
        self.assertIn('/api/v1/workout-plans/', content)
        self.assertIn('/api/v1/diet-plans/', content)
        self.assertIn('/api/v1/exercises/', content)
        self.assertIn('/api/v1/meals/', content)

    def test_api_docs_are_public(self):
        response = self.client.get(reverse('swagger-ui'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SoftDeleteTests(APITestCase):
    def setUp(self):
        self.user = create_user('alice')
        from workouts.models import Exercise, Workout

        self.Exercise = Exercise
        self.Workout = Workout
        self.exercise = Exercise.objects.create(
            name='Supino',
            description='Supino reto',
            sets=4,
            reps=10,
            muscle_group='peito',
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Treino A',
            description='Peito',
            duration=60,
            level='beginner',
        )

    def test_queryset_delete_is_soft(self):
        deleted, _ = self.Workout.objects.filter(pk=self.workout.pk).delete()

        self.assertEqual(deleted, 1)
        self.assertFalse(self.Workout.objects.filter(pk=self.workout.pk).exists())
        stored = self.Workout.all_objects.get(pk=self.workout.pk)
        self.assertFalse(stored.is_active)

    def test_restore_brings_record_back(self):
        self.workout.delete()

        self.workout.restore()

        self.assertTrue(self.Workout.objects.filter(pk=self.workout.pk).exists())

    def test_queryset_restore(self):
        self.Exercise.objects.filter(pk=self.exercise.pk).delete()

        self.Exercise.all_objects.filter(pk=self.exercise.pk).restore()

        self.assertTrue(self.Exercise.objects.filter(pk=self.exercise.pk).exists())

    def test_hard_delete_removes_row(self):
        self.workout.hard_delete()

        self.assertFalse(self.Workout.all_objects.filter(pk=self.workout.pk).exists())

    def test_soft_delete_does_not_remove_related_rows(self):
        self.workout.exercises.set([self.exercise])
        self.workout.delete()

        self.assertTrue(
            self.Exercise.all_objects.filter(pk=self.exercise.pk).exists()
        )
        self.assertTrue(
            self.Workout.all_objects.filter(
                pk=self.workout.pk, exercises=self.exercise
            ).exists()
        )

    def test_inactive_objects_are_hidden_from_default_manager(self):
        self.exercise.delete()

        self.assertEqual(self.Exercise.objects.count(), 0)
        self.assertEqual(self.Exercise.all_objects.count(), 1)

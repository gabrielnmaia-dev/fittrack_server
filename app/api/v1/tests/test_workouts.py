from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workouts.models import Exercise, Workout

from .utils import authenticate, create_user

WORKOUT_PAYLOAD = {
    'name': 'Treino A',
    'description': 'Peito e tríceps',
    'duration': 60,
    'level': 'intermediate',
}


class WorkoutTests(APITestCase):
    def setUp(self):
        self.alice = create_user('alice')
        self.bob = create_user('bob')
        self.staff = create_user('admin', is_staff=True)
        self.global_exercise = Exercise.objects.create(
            name='Supino',
            description='Supino reto',
            sets=4,
            reps=10,
            muscle_group='peito',
        )
        self.alice_exercise = Exercise.objects.create(
            user=self.alice,
            name='Crucifixo',
            description='Crucifixo com halteres',
            sets=3,
            reps=12,
            muscle_group='peito',
        )
        self.bob_exercise = Exercise.objects.create(
            user=self.bob,
            name='Remada',
            description='Remada curvada',
            sets=4,
            reps=10,
            muscle_group='costas',
        )
        self.alice_workout = Workout.objects.create(
            user=self.alice, **WORKOUT_PAYLOAD
        )
        self.alice_workout.exercises.set([self.global_exercise])
        self.bob_workout = Workout.objects.create(
            user=self.bob,
            **{**WORKOUT_PAYLOAD, 'name': 'Treino do Bob', 'level': 'advanced'},
        )
        self.list_url = reverse('workout-list')
        self.detail_url = reverse('workout-detail', args=[self.alice_workout.pk])

    def test_requires_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_only_returns_own_workouts(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Treino A')

    def test_staff_sees_all_workouts(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_create_assigns_owner_and_exercises(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**WORKOUT_PAYLOAD, 'exercises': [self.global_exercise.pk]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.alice.pk)
        self.assertEqual(
            response.data['exercise_details'][0]['name'], 'Supino'
        )
        workout = Workout.objects.get(pk=response.data['id'])
        self.assertEqual(workout.user, self.alice)

    def test_create_ignores_user_sent_by_client(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**WORKOUT_PAYLOAD, 'user': self.bob.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.alice.pk)

    def test_can_attach_own_and_global_exercises(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url,
            {'exercises': [self.global_exercise.pk, self.alice_exercise.pk]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.alice_workout.exercises.count(), 2)

    def test_cannot_attach_another_users_private_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url,
            {'exercises': [self.bob_exercise.pk]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exercises', response.data)

    def test_cannot_attach_inactive_exercise(self):
        self.global_exercise.is_active = False
        self.global_exercise.save(update_fields=['is_active'])
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**WORKOUT_PAYLOAD, 'exercises': [self.global_exercise.pk]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_another_users_workout_returns_404(self):
        authenticate(self.client, self.alice)

        response = self.client.get(
            reverse('workout-detail', args=[self.bob_workout.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_another_users_workout_returns_404(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('workout-detail', args=[self.bob_workout.pk]),
            {'name': 'Hackeado'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.bob_workout.refresh_from_db()
        self.assertEqual(self.bob_workout.name, 'Treino do Bob')

    def test_owner_can_update_workout(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url, {'duration': 90}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice_workout.refresh_from_db()
        self.assertEqual(self.alice_workout.duration, 90)

    def test_owner_can_soft_delete_workout(self):
        authenticate(self.client, self.alice)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(pk=self.alice_workout.pk).exists())
        stored = Workout.all_objects.get(pk=self.alice_workout.pk)
        self.assertFalse(stored.is_active)

    def test_filter_by_level(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url, {'level': 'advanced'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Treino do Bob')

    def test_search(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url, {'search': 'Bob'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_rejects_invalid_data(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**WORKOUT_PAYLOAD, 'duration': 0, 'level': 'unknown'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data)
        self.assertIn('level', response.data)

    def test_nested_exercise_details_are_read_only(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['exercise_details']), 1)

    def test_soft_deleted_exercise_disappears_from_workout(self):
        self.alice_workout.exercises.add(self.alice_exercise)
        self.alice_exercise.delete()
        authenticate(self.client, self.alice)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exercises'], [self.global_exercise.pk])
        self.assertEqual(
            [item['id'] for item in response.data['exercise_details']],
            [self.global_exercise.pk],
        )

    def test_cannot_see_another_users_workouts_in_filtered_list(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url, {'user': self.bob.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

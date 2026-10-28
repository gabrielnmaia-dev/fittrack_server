from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workouts.models import Exercise

from .utils import authenticate, create_user

EXERCISE_PAYLOAD = {
    'name': 'Supino reto',
    'description': 'Supino com barra',
    'sets': 4,
    'reps': 10,
    'muscle_group': 'peito',
}


class ExerciseTests(APITestCase):
    def setUp(self):
        self.alice = create_user('alice')
        self.bob = create_user('bob')
        self.staff = create_user('admin', is_staff=True)
        self.global_exercise = Exercise.objects.create(
            **{**EXERCISE_PAYLOAD, 'name': 'Agachamento', 'muscle_group': 'pernas'}
        )
        self.alice_exercise = Exercise.objects.create(
            user=self.alice, **EXERCISE_PAYLOAD
        )
        self.bob_exercise = Exercise.objects.create(
            user=self.bob, **{**EXERCISE_PAYLOAD, 'name': 'Remada'}
        )
        self.list_url = reverse('exercise-list')
        self.detail_url = reverse('exercise-detail', args=[self.alice_exercise.pk])

    def test_requires_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_returns_global_and_own_exercises_only(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url, {'page_size': 100})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {item['name'] for item in response.data['results']}
        self.assertEqual(names, {'Agachamento', 'Supino reto'})

    def test_create_sets_current_user_as_owner(self):
        authenticate(self.client, self.alice)

        response = self.client.post(self.list_url, EXERCISE_PAYLOAD, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.alice.pk)
        self.assertFalse(response.data['is_global'])
        self.assertTrue(
            Exercise.objects.filter(user=self.alice, name='Supino reto').exists()
        )

    def test_global_exercise_is_flagged(self):
        authenticate(self.client, self.alice)

        response = self.client.get(
            reverse('exercise-detail', args=[self.global_exercise.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_global'])
        self.assertIsNone(response.data['user'])

    def test_regular_user_cannot_update_global_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('exercise-detail', args=[self.global_exercise.pk]),
            {'name': 'Alterado'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.global_exercise.refresh_from_db()
        self.assertEqual(self.global_exercise.name, 'Agachamento')

    def test_regular_user_cannot_update_another_users_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('exercise-detail', args=[self.bob_exercise.pk]),
            {'name': 'Alterado'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_own_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url, {'sets': 5}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice_exercise.refresh_from_db()
        self.assertEqual(self.alice_exercise.sets, 5)

    def test_staff_can_update_global_exercise(self):
        authenticate(self.client, self.staff)

        response = self.client.patch(
            reverse('exercise-detail', args=[self.global_exercise.pk]),
            {'sets': 5},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.global_exercise.refresh_from_db()
        self.assertEqual(self.global_exercise.sets, 5)

    def test_owner_can_soft_delete_own_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Exercise.objects.filter(pk=self.alice_exercise.pk).exists())
        stored = Exercise.all_objects.get(pk=self.alice_exercise.pk)
        self.assertFalse(stored.is_active)

    def test_regular_user_cannot_delete_global_exercise(self):
        authenticate(self.client, self.alice)

        response = self.client.delete(
            reverse('exercise-detail', args=[self.global_exercise.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Exercise.objects.filter(pk=self.global_exercise.pk).exists()
        )

    def test_filter_by_muscle_group(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url, {'muscle_group': 'peito'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Supino reto')

    def test_search_and_ordering(self):
        authenticate(self.client, self.alice)

        response = self.client.get(
            self.list_url, {'search': 'agach', 'ordering': 'name'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        ordered = self.client.get(self.list_url, {'ordering': 'name', 'page_size': 100})
        names = [item['name'] for item in ordered.data['results']]
        self.assertEqual(names, sorted(names))

    def test_rejects_invalid_values(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**EXERCISE_PAYLOAD, 'sets': 0, 'reps': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sets', response.data)
        self.assertIn('reps', response.data)

    def test_pagination_and_page_size(self):
        Exercise.objects.bulk_create(
            [
                Exercise(
                    name=f'Exercício {index}',
                    description='x',
                    sets=3,
                    reps=12,
                    muscle_group='costas',
                )
                for index in range(15)
            ]
        )
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url, {'page_size': 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertGreaterEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])

    def test_page_size_is_capped(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url, {'page_size': 1000})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 100)

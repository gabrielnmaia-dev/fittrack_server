from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from diet.models import DietPlan, Meal

from .utils import authenticate, create_user

PLAN_PAYLOAD = {
    'name': 'Plano de ganho',
    'description': 'Dieta hipercalórica',
    'calories': 3000,
}

MEAL_PAYLOAD = {
    'name': 'Café da manhã',
    'description': 'Ovos e aveia',
    'calories': 600,
}


class DietPlanTests(APITestCase):
    def setUp(self):
        self.alice = create_user('alice')
        self.bob = create_user('bob')
        self.staff = create_user('admin', is_staff=True)
        self.alice_plan = DietPlan.objects.create(user=self.alice, **PLAN_PAYLOAD)
        self.bob_plan = DietPlan.objects.create(
            user=self.bob, **{**PLAN_PAYLOAD, 'name': 'Plano do Bob'}
        )
        self.alice_meal = Meal.objects.create(
            diet_plan=self.alice_plan, **MEAL_PAYLOAD
        )
        self.bob_meal = Meal.objects.create(
            diet_plan=self.bob_plan, **{**MEAL_PAYLOAD, 'name': 'Refeição do Bob'}
        )
        self.list_url = reverse('dietplan-list')
        self.detail_url = reverse('dietplan-detail', args=[self.alice_plan.pk])

    def test_requires_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_only_returns_own_plans(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Plano de ganho')

    def test_staff_sees_all_plans(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_create_assigns_owner(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**PLAN_PAYLOAD, 'name': 'Novo plano', 'user': self.bob.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.alice.pk)
        self.assertEqual(DietPlan.objects.get(pk=response.data['id']).user, self.alice)

    def test_nested_meals_are_returned(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['meals']), 1)
        self.assertEqual(response.data['meals'][0]['name'], 'Café da manhã')

    def test_soft_deleted_meal_disappears_from_plan(self):
        self.alice_meal.delete()
        authenticate(self.client, self.alice)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meals'], [])

    def test_retrieve_another_users_plan_returns_404(self):
        authenticate(self.client, self.alice)

        response = self.client.get(
            reverse('dietplan-detail', args=[self.bob_plan.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_another_users_plan_returns_404(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('dietplan-detail', args=[self.bob_plan.pk]),
            {'name': 'Hackeado'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_and_delete_plan(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url, {'calories': 3200}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(self.detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DietPlan.objects.filter(pk=self.alice_plan.pk).exists())
        self.assertFalse(
            DietPlan.all_objects.get(pk=self.alice_plan.pk).is_active
        )

    def test_rejects_invalid_calories(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url, {**PLAN_PAYLOAD, 'calories': 0}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('calories', response.data)

    def test_search(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url, {'search': 'Bob'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class MealTests(APITestCase):
    def setUp(self):
        self.alice = create_user('alice')
        self.bob = create_user('bob')
        self.staff = create_user('admin', is_staff=True)
        self.alice_plan = DietPlan.objects.create(user=self.alice, **PLAN_PAYLOAD)
        self.bob_plan = DietPlan.objects.create(
            user=self.bob, **{**PLAN_PAYLOAD, 'name': 'Plano do Bob'}
        )
        self.alice_meal = Meal.objects.create(
            diet_plan=self.alice_plan, **MEAL_PAYLOAD
        )
        self.bob_meal = Meal.objects.create(
            diet_plan=self.bob_plan, **{**MEAL_PAYLOAD, 'name': 'Refeição do Bob'}
        )
        self.list_url = reverse('meal-list')
        self.detail_url = reverse('meal-detail', args=[self.alice_meal.pk])

    def test_requires_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_only_returns_meals_from_own_plans(self):
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Café da manhã')

    def test_create_meal_in_own_plan(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**MEAL_PAYLOAD, 'name': 'Almoço', 'diet_plan': self.alice_plan.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Meal.objects.filter(
                diet_plan=self.alice_plan, name='Almoço'
            ).exists()
        )

    def test_cannot_create_meal_in_another_users_plan(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**MEAL_PAYLOAD, 'diet_plan': self.bob_plan.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('diet_plan', response.data)
        self.assertFalse(
            Meal.objects.filter(diet_plan=self.bob_plan, name='Café da manhã').exists()
        )

    def test_cannot_move_meal_to_another_users_plan(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            self.detail_url,
            {'diet_plan': self.bob_plan.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alice_meal.refresh_from_db()
        self.assertEqual(self.alice_meal.diet_plan, self.alice_plan)

    def test_cannot_access_another_users_meal(self):
        authenticate(self.client, self.alice)

        response = self.client.get(
            reverse('meal-detail', args=[self.bob_meal.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_another_users_meal(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('meal-detail', args=[self.bob_meal.pk]),
            {'name': 'Hackeado'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_meal_softly(self):
        authenticate(self.client, self.alice)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Meal.objects.filter(pk=self.alice_meal.pk).exists())
        self.assertFalse(Meal.all_objects.get(pk=self.alice_meal.pk).is_active)

    def test_meals_of_deleted_plan_are_hidden(self):
        self.alice_plan.delete()
        authenticate(self.client, self.alice)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        # The meal row itself is still present in the database.
        self.assertTrue(Meal.all_objects.filter(pk=self.alice_meal.pk).exists())

    def test_filter_by_diet_plan(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url, {'diet_plan': self.alice_plan.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_staff_sees_all_meals(self):
        authenticate(self.client, self.staff)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_rejects_invalid_calories(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**MEAL_PAYLOAD, 'calories': 0, 'diet_plan': self.alice_plan.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('calories', response.data)

    def test_rejects_invalid_plan_reference(self):
        authenticate(self.client, self.alice)

        response = self.client.post(
            self.list_url,
            {**MEAL_PAYLOAD, 'diet_plan': 999999},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('diet_plan', response.data)

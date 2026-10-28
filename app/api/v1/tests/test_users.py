from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import (
    STRONG_PASSWORD,
    authenticate,
    create_profile,
    create_user,
    registration_payload,
)

User = get_user_model()


class UserMeTests(APITestCase):
    def setUp(self):
        self.user = create_user('alice')
        self.profile = create_profile(self.user)
        self.me_url = reverse('user-me')

    def test_me_requires_authentication(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_own_user_with_profile(self):
        authenticate(self.client, self.user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['profile']['weight'], 80.0)
        self.assertNotIn('password', response.data)

    def test_me_patch_updates_nested_profile(self):
        authenticate(self.client, self.user)

        response = self.client.patch(
            self.me_url,
            {'profile': {'weight': 82.5, 'goal': 'lose_weight'}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.weight, 82.5)
        self.assertEqual(self.profile.goal, 'lose_weight')
        self.assertEqual(self.profile.age, 30)

    def test_me_patch_creates_profile_when_missing(self):
        user = create_user('noprofile')
        authenticate(self.client, user)

        response = self.client.patch(
            self.me_url,
            {'profile': {'age': 25, 'height': 170, 'weight': 70, 'goal': 'maintain_weight'}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(hasattr(user, 'profile'))

    def test_me_patch_rejects_invalid_profile(self):
        authenticate(self.client, self.user)

        response = self.client.patch(
            self.me_url,
            {'profile': {'age': 0}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)

    def test_me_patch_changes_password_with_hash(self):
        authenticate(self.client, self.user)
        new_password = 'N3w-Str0ng-Pass!'

        response = self.client.patch(
            self.me_url,
            {'password': new_password},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_me_patch_cannot_set_is_staff(self):
        authenticate(self.client, self.user)

        response = self.client.patch(
            self.me_url,
            {'is_staff': True, 'is_superuser': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_me_rejects_deleted_user(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        authenticate(self.client, self.user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAccessTests(APITestCase):
    def setUp(self):
        self.alice = create_user('alice')
        self.bob = create_user('bob')
        self.staff = create_user('admin', is_staff=True)
        create_profile(self.alice)
        create_profile(self.bob)

    def test_regular_user_cannot_list_users(self):
        authenticate(self.client, self.alice)

        response = self.client.get(reverse('user-list'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_retrieve_another_user(self):
        authenticate(self.client, self.alice)

        response = self.client.get(reverse('user-detail', args=[self.bob.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_user_cannot_update_another_user(self):
        authenticate(self.client, self.alice)

        response = self.client.patch(
            reverse('user-detail', args=[self.bob.pk]),
            {'first_name': 'Hacked'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.bob.refresh_from_db()
        self.assertEqual(self.bob.first_name, '')

    def test_regular_user_can_retrieve_themselves_by_id(self):
        authenticate(self.client, self.alice)

        response = self.client.get(reverse('user-detail', args=[self.alice.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_delete_any_user(self):
        authenticate(self.client, self.alice)

        response = self.client.delete(reverse('user-detail', args=[self.alice.pk]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_list_and_search_users(self):
        authenticate(self.client, self.staff)

        response = self.client.get(reverse('user-list'), {'search': 'alice'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['username'], 'alice')

    def test_staff_deactivates_user_instead_of_deleting(self):
        authenticate(self.client, self.staff)

        response = self.client.delete(reverse('user-detail', args=[self.bob.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.bob.refresh_from_db()
        self.assertFalse(self.bob.is_active)
        self.assertTrue(User.objects.filter(pk=self.bob.pk).exists())

    def test_staff_can_filter_inactive_users(self):
        self.bob.is_active = False
        self.bob.save(update_fields=['is_active'])
        authenticate(self.client, self.staff)

        response = self.client.get(reverse('user-list'), {'is_active': 'false'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [item['username'] for item in response.data['results']]
        self.assertEqual(usernames, ['bob'])

    def test_registration_response_does_not_leak_password(self):
        response = self.client.post(
            reverse('register'), registration_payload(), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertNotIn(STRONG_PASSWORD, str(response.data))

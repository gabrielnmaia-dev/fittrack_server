from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import (
    STRONG_PASSWORD,
    create_user,
    registration_payload,
)

User = get_user_model()


class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse('register')

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            self.url, registration_payload(), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertTrue(response.data['is_staff'] is False)
        self.assertEqual(response.data['profile']['goal'], 'gain_muscle')

        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertTrue(hasattr(user, 'profile'))

    def test_register_is_also_available_on_users_endpoint(self):
        response = self.client.post(
            reverse('user-list'), registration_payload('another'), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='another').exists())

    def test_register_duplicate_username(self):
        create_user('duplicated')

        response = self.client.post(
            self.url, registration_payload('duplicated'), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            self.url,
            registration_payload(password='123456'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_rejects_invalid_profile_data(self):
        response = self.client.post(
            self.url,
            registration_payload(profile={'age': 0, 'height': 10, 'weight': 0, 'goal': 'invalid'}),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)

    def test_register_without_profile_is_allowed(self):
        payload = registration_payload()
        payload.pop('profile')

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser')
        self.assertFalse(hasattr(user, 'profile'))

    def test_register_cannot_escalate_privileges(self):
        payload = registration_payload(is_staff=True, is_superuser=True)

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_ignores_invalid_authorization_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')

        response = self.client.post(
            self.url, registration_payload('withtoken'), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='withtoken').exists())


class TokenTests(APITestCase):
    def setUp(self):
        self.user = create_user('tester')
        self.obtain_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_obtain_and_refresh_token(self):
        response = self.client.post(
            self.obtain_url,
            {'username': 'tester', 'password': STRONG_PASSWORD},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        refresh_response = self.client.post(
            self.refresh_url,
            {'refresh': response.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_obtain_token_with_invalid_credentials(self):
        response = self.client.post(
            self.obtain_url,
            {'username': 'tester', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_obtain_token(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        response = self.client.post(
            self.obtain_url,
            {'username': 'tester', 'password': STRONG_PASSWORD},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_requires_authentication(self):
        response = self.client.get(reverse('workout-list'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_grants_access(self):
        token_response = self.client.post(
            self.obtain_url,
            {'username': 'tester', 'password': STRONG_PASSWORD},
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get(reverse('workout-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

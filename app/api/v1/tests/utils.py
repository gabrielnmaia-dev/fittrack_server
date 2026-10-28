"""Shared helpers for the API test suite."""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile

User = get_user_model()

STRONG_PASSWORD = 'Str0ng-Pass!2026'


def create_user(username='alice', password=STRONG_PASSWORD, **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


def create_profile(user, **overrides):
    data = {
        'age': 30,
        'height': 180.0,
        'weight': 80.0,
        'goal': 'gain_muscle',
    }
    data.update(overrides)
    return UserProfile.objects.create(user=user, **data)


def profile_payload(**overrides):
    data = {
        'age': 30,
        'height': 180.0,
        'weight': 80.0,
        'goal': 'gain_muscle',
    }
    data.update(overrides)
    return data


def registration_payload(username='newuser', **overrides):
    data = {
        'username': username,
        'email': f'{username}@example.com',
        'password': STRONG_PASSWORD,
        'profile': profile_payload(),
    }
    data.update(overrides)
    return data


def authenticate(client, user):
    """Authenticate the test client with a valid JWT for ``user``."""
    access = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return access

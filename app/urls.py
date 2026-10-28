"""Root URL configuration for the FitTrack API."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.api.v1.viewsets import RegisterView
from core.views import health

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication
    path(
        'api/v1/auth/register/',
        RegisterView.as_view(),
        name='register',
    ),
    path(
        'api/v1/auth/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'api/v1/auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    # API v1
    path('api/v1/', include('app.api.v1.router')),
    # Health check (infrastructure)
    path('health/', health, name='health'),
    path('api/v1/health/', health, name='health-api'),
    # Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from knox import views as knox_views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .viewsets import StudentViewSet, SupervisorViewSet, ThesisViewSet, CommentViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='api-student')
router.register(r'supervisors', SupervisorViewSet, basename='api-supervisor')
router.register(r'theses', ThesisViewSet, basename='api-thesis')
router.register(r'comments', CommentViewSet, basename='api-comment')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),

    # Token management endpoints
    path('auth/login/', knox_views.LoginView.as_view(), name='knox_login'),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('auth/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    # API documentation endpoints
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),
]

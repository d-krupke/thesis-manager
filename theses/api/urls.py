"""
API URLS.PY - REST API URL Configuration
=========================================

This file defines URL routing for the REST API.
Unlike the main urls.py (which routes to HTML views), this routes to API endpoints.

WHAT BELONGS HERE:
------------------
1. API endpoint URL patterns
2. Router registration for ViewSets
3. Authentication endpoints (login/logout)
4. API documentation endpoints

REST FRAMEWORK ROUTER:
----------------------
The router automatically creates URL patterns for ViewSets:

router.register(r'students', StudentViewSet)

This AUTOMATICALLY creates these URLs:
- GET    /api/students/          → List all students
- POST   /api/students/          → Create new student
- GET    /api/students/{id}/     → Get student details
- PUT    /api/students/{id}/     → Update student
- PATCH  /api/students/{id}/     → Partial update
- DELETE /api/students/{id}/     → Delete student

Plus any custom @action endpoints defined in the ViewSet!

ROUTER vs MANUAL URLS:
----------------------
- Router: Use for ViewSets (automatic URL generation)
- Manual path(): Use for custom views or one-off endpoints

KNOX AUTHENTICATION:
--------------------
Knox provides token-based authentication for the API:
- Login returns a token that clients use for subsequent requests
- Logout invalidates the current token
- LogoutAll invalidates all tokens for the user

API DOCUMENTATION:
------------------
drf-spectacular generates interactive API documentation:
- /api/schema/  → OpenAPI schema (JSON/YAML)
- /api/docs/    → Swagger UI (interactive documentation)
- /api/redoc/   → ReDoc (alternative documentation format)

These are auto-generated from your ViewSets, serializers, and docstrings!

ACCESSING THE API:
------------------
1. Get a token:
   POST /api/auth/login/
   Body: {"username": "...", "password": "..."}
   Response: {"token": "abc123..."}

2. Use the token:
   GET /api/students/
   Header: Authorization: Token abc123...

3. Logout:
   POST /api/auth/logout/
   Header: Authorization: Token abc123...
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from knox import views as knox_views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .viewsets import StudentViewSet, SupervisorViewSet, ThesisViewSet, CommentViewSet

# DefaultRouter: Creates URL patterns for all ViewSets
# Includes a default API root view that lists all endpoints
router = DefaultRouter()

# Register ViewSets with the router
# Format: router.register(r'url-prefix', ViewSetClass, basename='url-name-prefix')
#
# Each registration creates multiple URLs:
# - List/Create: /api/{url-prefix}/
# - Retrieve/Update/Delete: /api/{url-prefix}/{id}/
# - Custom actions: /api/{url-prefix}/{id}/{action-name}/
router.register(r'students', StudentViewSet, basename='api-student')
router.register(r'supervisors', SupervisorViewSet, basename='api-supervisor')
router.register(r'theses', ThesisViewSet, basename='api-thesis')
router.register(r'comments', CommentViewSet, basename='api-comment')

urlpatterns = [
    # Include all router URLs
    # This adds: /api/students/, /api/theses/, etc.
    path('', include(router.urls)),

    # Knox token authentication endpoints
    # These endpoints handle API authentication (not the web login)
    path('auth/login/', knox_views.LoginView.as_view(), name='knox_login'),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('auth/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    # API documentation endpoints (powered by drf-spectacular)
    # Visit /api/docs/ in your browser to see interactive API documentation
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),  # OpenAPI schema
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),  # Swagger UI
    path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),  # ReDoc UI
]

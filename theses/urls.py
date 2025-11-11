"""
URLS.PY - URL Routing Configuration
====================================

This file maps URLs to views. When a user visits a URL, Django matches it
against these patterns and calls the corresponding view.

WHAT BELONGS HERE:
------------------
1. URL patterns (path or re_path)
2. Name assignments for URLs (for reverse lookup)
3. URL parameters (like <int:pk>)

URL PATTERNS:
-------------
path('url/', view, name='url_name')

- First argument: URL pattern as string
- Second argument: View function or .as_view() for class-based views
- name: Used for reverse lookup in templates and code

URL PARAMETERS:
---------------
- <int:pk>: Captures an integer, passes it as 'pk' to the view
- <str:slug>: Captures a string (letters, numbers, hyphens, underscores)
- <uuid:id>: Captures a UUID
- <path:url>: Captures any string including slashes

Examples:
- path('thesis/5/', ...) matches exact URL
- path('thesis/<int:pk>/', ...) matches /thesis/1/, /thesis/999/, etc.
- path('search/<str:query>/', ...) matches /search/machine-learning/, etc.

REVERSE URL LOOKUP:
-------------------
Instead of hardcoding URLs, use the 'name' for reverse lookup:

In templates:
    {% url 'thesis_detail' pk=5 %}  → /thesis/5/

In Python code:
    reverse('thesis_detail', kwargs={'pk': 5})  → '/thesis/5/'

In models:
    def get_absolute_url(self):
        return reverse('thesis_detail', kwargs={'pk': self.pk})

HOW TO ADD A NEW URL:
---------------------
1. Add a path() to urlpatterns list
2. Give it a unique name
3. Map it to a view
4. Use URL parameters if needed

Example:
    path('thesis/<int:pk>/archive/', views.archive_thesis, name='thesis_archive'),
"""

from django.urls import path
from . import views

# urlpatterns is a list of URL patterns Django will try to match (in order)
urlpatterns = [
    # Root URL (homepage) - matches http://localhost/
    path('', views.ThesisListView.as_view(), name='thesis_list'),

    # Thesis URLs
    # <int:pk>: Captures the thesis ID from URL, passes to view as pk parameter
    # Example: /thesis/5/ captures pk=5
    path('thesis/<int:pk>/', views.ThesisDetailView.as_view(), name='thesis_detail'),
    path('thesis/new/', views.ThesisCreateView.as_view(), name='thesis_create'),
    path('thesis/<int:pk>/edit/', views.ThesisUpdateView.as_view(), name='thesis_update'),

    # Student URLs
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('student/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('student/new/', views.StudentCreateView.as_view(), name='student_create'),
    path('student/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),

    # Supervisor URLs
    path('supervisors/', views.SupervisorListView.as_view(), name='supervisor_list'),
    path('supervisor/<int:pk>/', views.SupervisorDetailView.as_view(), name='supervisor_detail'),
    path('supervisor/new/', views.SupervisorCreateView.as_view(), name='supervisor_create'),
    path('supervisor/<int:pk>/edit/', views.SupervisorUpdateView.as_view(), name='supervisor_update'),

    # Comment URLs
    path('thesis/<int:thesis_pk>/comment/add/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),

    # API Token Management URLs
    path('api-tokens/', views.api_tokens_list, name='api_tokens_list'),
    path('api-tokens/create/', views.api_token_create, name='api_token_create'),
    path('api-tokens/<str:token_id>/delete/', views.api_token_delete, name='api_token_delete'),
    path('api-tokens/delete-all/', views.api_tokens_delete_all, name='api_tokens_delete_all'),

    # CSV Export URL
    path('theses/export/', views.export_theses_csv, name='export_theses_csv'),

    # Admin User Management URLs
    path('users/create/', views.AdminCreateUserView.as_view(), name='admin_create_user'),

    # Feedback Request URLs
    path('thesis/<int:thesis_pk>/request-feedback/', views.feedback_request_create, name='feedback_request_create'),
    path('feedback/<str:token>/', views.feedback_respond, name='feedback_respond'),
]

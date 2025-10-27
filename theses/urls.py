from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.ThesisListView.as_view(), name='thesis_list'),

    # Thesis URLs
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
]

"""
API VIEWSETS.PY - REST API Endpoints
=====================================

This file defines VIEWSETS - the REST API endpoints for the application.
ViewSets are like Views, but for REST APIs instead of HTML pages.

WHAT BELONGS HERE:
------------------
1. ViewSet classes (ModelViewSet, ReadOnlyModelViewSet)
2. API endpoint logic (list, retrieve, create, update, delete)
3. Custom API actions (@action decorator)
4. API-specific business logic
5. Filtering, searching, and ordering configuration

VIEWSETS vs VIEWS:
------------------
- Views (views.py): Return HTML pages for web browsers
- ViewSets (this file): Return JSON data for API clients

WHAT IS A REST API?
-------------------
A REST API allows programs (not humans) to interact with your application:
- GET /api/theses/     → List all theses (as JSON)
- GET /api/theses/5/   → Get thesis #5 details (as JSON)
- POST /api/theses/    → Create new thesis (send JSON, get JSON back)
- PUT /api/theses/5/   → Update thesis #5 (send JSON)
- DELETE /api/theses/5/ → Delete thesis #5

MODELVIEWSET:
-------------
ModelViewSet automatically provides these actions:
- list(): GET /api/resource/          (get all items)
- retrieve(): GET /api/resource/5/    (get one item)
- create(): POST /api/resource/       (create new item)
- update(): PUT /api/resource/5/      (full update)
- partial_update(): PATCH /api/resource/5/  (partial update)
- destroy(): DELETE /api/resource/5/  (delete item)

COMMON VIEWSET ATTRIBUTES:
--------------------------
- queryset: Which objects to include (like get_queryset in views.py)
- serializer_class: Which serializer to use (like forms in views.py)
- permission_classes: Who can access this endpoint
- filter_backends: Enable filtering, searching, ordering
- filterset_fields: Which fields can be filtered
- search_fields: Which fields to search in
- ordering_fields: Which fields can be used for sorting

CUSTOM ACTIONS:
---------------
Use @action decorator to add custom endpoints:

@action(detail=True, methods=['get'])
def custom_endpoint(self, request, pk=None):
    # This creates: GET /api/resource/5/custom_endpoint/
    ...

- detail=True: Operates on a single object (needs pk)
- detail=False: Operates on the collection (no pk needed)
- methods=['get', 'post']: Which HTTP methods to accept

EXAMPLE:
--------
class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def special_data(self, request, pk=None):
        obj = self.get_object()
        return Response({'data': obj.calculate_something()})
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from theses.models import Student, Supervisor, Thesis, Comment
from .serializers import (
    StudentSerializer, StudentListSerializer,
    SupervisorSerializer, SupervisorListSerializer,
    ThesisSerializer, ThesisListSerializer, ThesisCreateUpdateSerializer,
    CommentSerializer
)
from .permissions import IsStaffOrReadOnly, IsSupervisorOrReadOnly, IsOwnerOrReadOnly


# @extend_schema_view: Adds API documentation for Swagger/ReDoc
# These descriptions appear in the auto-generated API docs
@extend_schema_view(
    list=extend_schema(description="List all students"),
    retrieve=extend_schema(description="Get student details"),
    create=extend_schema(description="Create a new student"),
    update=extend_schema(description="Update a student"),
    partial_update=extend_schema(description="Partially update a student"),
    destroy=extend_schema(description="Delete a student"),
)
class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing students.

    Provides standard CRUD operations for students.
    Only staff users can create, update, or delete students.

    Endpoints created by this ViewSet:
    - GET    /api/students/       → List all students
    - POST   /api/students/       → Create new student (staff only)
    - GET    /api/students/5/     → Get student details
    - PUT    /api/students/5/     → Update student (staff only)
    - PATCH  /api/students/5/     → Partial update (staff only)
    - DELETE /api/students/5/     → Delete student (staff only)
    - GET    /api/students/5/theses/ → Get student's theses (custom action)
    """
    # queryset: All students from the database
    queryset = Student.objects.all()

    # permission_classes: List of permission checks (ALL must pass)
    # - IsAuthenticated: User must be logged in
    # - IsStaffOrReadOnly: Staff can edit, others can only read
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]

    # filter_backends: Enable filtering and searching
    # These allow URL parameters like ?search=john&ordering=last_name
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # search_fields: Which fields to search (for ?search=query)
    # Example: /api/students/?search=john → searches in these fields
    search_fields = ['first_name', 'last_name', 'email', 'student_id']

    # ordering_fields: Which fields can be used for sorting
    # Example: /api/students/?ordering=-last_name (minus = descending)
    ordering_fields = ['last_name', 'first_name', 'created_at']

    # ordering: Default sort order (if no ?ordering= parameter)
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        """
        Choose which serializer to use based on the action.

        - List view: Use simplified StudentListSerializer (faster)
        - Detail/Create/Update: Use full StudentSerializer (more data)

        This is like using different forms for different views.
        """
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer

    # @action: Creates a custom endpoint
    # detail=True: Operates on single student (/api/students/5/theses/)
    # methods=['get']: Only accepts GET requests
    @extend_schema(
        description="Get all theses for this student",
        responses={200: ThesisListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def theses(self, request, pk=None):
        """
        Custom endpoint: Get all theses for a specific student.

        URL: /api/students/{id}/theses/
        Example: /api/students/5/theses/ → Returns all theses for student #5
        """
        # self.get_object(): Gets the student based on pk from URL
        student = self.get_object()
        # Access related theses through the ManyToMany relationship
        theses = student.theses.all()
        # Serialize the theses to JSON
        serializer = ThesisListSerializer(theses, many=True, context={'request': request})
        # Return JSON response
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List all supervisors"),
    retrieve=extend_schema(description="Get supervisor details"),
    create=extend_schema(description="Create a new supervisor"),
    update=extend_schema(description="Update a supervisor"),
    partial_update=extend_schema(description="Partially update a supervisor"),
    destroy=extend_schema(description="Delete a supervisor"),
)
class SupervisorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing supervisors.

    Similar to StudentViewSet but for supervisors.
    Only staff users can create, update, or delete supervisors.
    """
    queryset = Supervisor.objects.all()
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        """Choose serializer: simplified for list, full for details"""
        if self.action == 'list':
            return SupervisorListSerializer
        return SupervisorSerializer

    @extend_schema(
        description="Get all theses supervised by this supervisor",
        responses={200: ThesisListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def theses(self, request, pk=None):
        """
        Custom endpoint: /api/supervisors/{id}/theses/
        Returns all theses supervised by this supervisor.
        """
        supervisor = self.get_object()
        # Note: Uses 'supervised_theses' (the related_name from Thesis model)
        theses = supervisor.supervised_theses.all()
        serializer = ThesisListSerializer(theses, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="List all theses with optional filtering",
        parameters=[
            OpenApiParameter(name='phase', description='Filter by phase', required=False, type=str),
            OpenApiParameter(name='thesis_type', description='Filter by thesis type', required=False, type=str),
            OpenApiParameter(name='student', description='Filter by student ID', required=False, type=int),
            OpenApiParameter(name='supervisor', description='Filter by supervisor ID', required=False, type=int),
        ]
    ),
    retrieve=extend_schema(description="Get thesis details including comments"),
    create=extend_schema(description="Create a new thesis"),
    update=extend_schema(description="Update a thesis"),
    partial_update=extend_schema(description="Partially update a thesis"),
    destroy=extend_schema(description="Delete a thesis"),
)
class ThesisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing theses.

    This is the main ViewSet with the most features:
    - Advanced filtering by phase, type, student, supervisor
    - Search across title and student names
    - Custom actions for comments
    - Permission checks: supervisors can edit their theses

    Endpoints:
    - GET    /api/theses/              → List with filters
    - POST   /api/theses/              → Create new thesis
    - GET    /api/theses/5/            → Get details
    - PUT    /api/theses/5/            → Update (supervisor/staff)
    - PATCH  /api/theses/5/            → Partial update (supervisor/staff)
    - DELETE /api/theses/5/            → Delete (staff only)
    - GET    /api/theses/5/comments/   → Get all comments
    - POST   /api/theses/5/add_comment/ → Add a comment
    """
    # prefetch_related: Load related data efficiently (avoids N+1 queries)
    queryset = Thesis.objects.prefetch_related('students', 'supervisors', 'comments').all()

    # IsSupervisorOrReadOnly: Allows supervisors to edit their own theses
    permission_classes = [IsAuthenticated, IsSupervisorOrReadOnly]

    # DjangoFilterBackend: Enables filtering by exact field values
    # Example: /api/theses/?phase=registered&thesis_type=bachelor
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # filterset_fields: Which fields can be filtered with ?field=value
    filterset_fields = ['phase', 'thesis_type', 'students', 'supervisors']

    # search_fields: Full-text search with ?search=query
    # Double underscore (__) accesses related fields: students__first_name
    search_fields = ['title', 'students__first_name', 'students__last_name', 'description']

    # ordering_fields: Which fields can be sorted with ?ordering=field
    ordering_fields = ['date_first_contact', 'date_registration', 'date_deadline', 'created_at']

    # Default ordering: newest first (minus = descending)
    ordering = ['-date_first_contact', '-created_at']

    def get_serializer_class(self):
        """
        Choose appropriate serializer based on action.

        - List: Simplified data (faster, less info)
        - Create/Update: Only writable fields
        - Retrieve: Full details with nested relationships
        """
        if self.action == 'list':
            return ThesisListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ThesisCreateUpdateSerializer
        return ThesisSerializer

    def perform_update(self, serializer):
        """
        Called when updating a thesis via PUT or PATCH.

        Sets the current user on the instance so that auto-generated comments
        from signals can track who made the changes.
        """
        serializer.instance._current_user = self.request.user
        serializer.save()

    @extend_schema(
        description="Get all comments for this thesis",
        responses={200: CommentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        Custom endpoint: /api/theses/{id}/comments/
        Returns all comments for a specific thesis.
        """
        thesis = self.get_object()
        comments = thesis.comments.all()
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        description="Add a comment to this thesis",
        request=CommentSerializer,
        responses={201: CommentSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """
        Custom endpoint: POST /api/theses/{id}/add_comment/
        Add a new comment to a specific thesis.

        The thesis and user are automatically set from the URL and request.
        Accepts optional 'is_auto_generated' field to mark automated comments.
        """
        thesis = self.get_object()

        # Create a mutable copy of request data and add thesis ID
        # This ensures validation passes while thesis is automatically set
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['thesis'] = thesis.id

        # Deserialize the incoming JSON data
        serializer = CommentSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            # Save with additional fields not in the request
            # Allow is_auto_generated to be set via request data (defaults to False)
            is_auto_generated = request.data.get('is_auto_generated', False)
            serializer.save(user=request.user, is_auto_generated=is_auto_generated)
            # Return 201 Created with the new comment data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Return 400 Bad Request with validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description="List all comments"),
    retrieve=extend_schema(description="Get comment details"),
    create=extend_schema(description="Create a new comment"),
    update=extend_schema(description="Update a comment"),
    partial_update=extend_schema(description="Partially update a comment"),
    destroy=extend_schema(description="Delete a comment"),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing comments.

    Permission rules:
    - Users can only edit/delete their own comments
    - All authenticated users can view and create comments

    Filtering options:
    - ?thesis=5          → Show comments for thesis #5
    - ?user=3            → Show comments by user #3
    - ?is_auto_generated=true → Show only auto-generated comments
    """
    # select_related: Efficiently load related user and thesis (reduces queries)
    queryset = Comment.objects.select_related('user', 'thesis').all()

    serializer_class = CommentSerializer

    # IsOwnerOrReadOnly: Users can only edit their own comments
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    # filterset_fields: Allow filtering by these fields
    # Example: /api/comments/?thesis=5&is_auto_generated=false
    filterset_fields = ['thesis', 'user', 'is_auto_generated']

    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']  # Newest first

    def perform_create(self, serializer):
        """
        Called when creating a new comment via POST.

        Automatically sets the user field to the current user.
        This prevents users from creating comments as other users.
        """
        serializer.save(user=self.request.user)

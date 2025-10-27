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
    """
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'student_id']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer

    @extend_schema(
        description="Get all theses for this student",
        responses={200: ThesisListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def theses(self, request, pk=None):
        """Get all theses for a specific student"""
        student = self.get_object()
        theses = student.theses.all()
        serializer = ThesisListSerializer(theses, many=True, context={'request': request})
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

    Provides standard CRUD operations for supervisors.
    Only staff users can create, update, or delete supervisors.
    """
    queryset = Supervisor.objects.all()
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return SupervisorListSerializer
        return SupervisorSerializer

    @extend_schema(
        description="Get all theses supervised by this supervisor",
        responses={200: ThesisListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def theses(self, request, pk=None):
        """Get all theses supervised by a specific supervisor"""
        supervisor = self.get_object()
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

    Provides standard CRUD operations for theses.
    Supervisors can edit theses they supervise.
    Staff users can edit any thesis.
    All authenticated users can view theses.
    """
    queryset = Thesis.objects.prefetch_related('students', 'supervisors', 'comments').all()
    permission_classes = [IsAuthenticated, IsSupervisorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['phase', 'thesis_type', 'students', 'supervisors']
    search_fields = ['title', 'students__first_name', 'students__last_name', 'description']
    ordering_fields = ['date_first_contact', 'date_registration', 'date_deadline', 'created_at']
    ordering = ['-date_first_contact', '-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ThesisListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ThesisCreateUpdateSerializer
        return ThesisSerializer

    @extend_schema(
        description="Get all comments for this thesis",
        responses={200: CommentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for a specific thesis"""
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
        """Add a new comment to a specific thesis"""
        thesis = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(thesis=thesis, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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

    Users can edit their own comments.
    All authenticated users can view comments.
    """
    queryset = Comment.objects.select_related('user', 'thesis').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['thesis', 'user', 'is_auto_generated']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

"""
API SERIALIZERS.PY - Data Transformation for API
=================================================

Serializers convert Django models to/from JSON for the API.
Think of them as translators between Python objects and JSON.

WHAT BELONGS HERE:
------------------
1. Serializer classes (usually ModelSerializer)
2. Field definitions and customizations
3. Validation logic for API inputs
4. Computed/read-only fields

SERIALIZERS vs FORMS:
---------------------
- Forms: For HTML forms in web interface
- Serializers: For JSON data in REST API
- Similar concepts, different use cases

HOW SERIALIZERS WORK:
---------------------
1. Deserialization (JSON → Python):
   - Receive JSON from API request
   - Validate the data
   - Convert to Python objects
   - Save to database

2. Serialization (Python → JSON):
   - Read from database
   - Convert to Python dict
   - Return as JSON to API client

COMMON FIELD TYPES:
-------------------
- CharField: Text fields
- IntegerField: Numbers
- DateField/DateTimeField: Dates
- BooleanField: True/False
- SerializerMethodField: Custom computed fields
- PrimaryKeyRelatedField: References to other models (IDs)
- Nested serializers: Full objects instead of just IDs

EXAMPLE:
--------
class MySerializer(serializers.ModelSerializer):
    # Custom computed field
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = MyModel
        fields = ['id', 'name', 'full_name']
        read_only_fields = ['id']  # Can't be changed via API

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from theses.models import Student, Supervisor, Thesis, Comment, FeedbackTemplate, FeedbackRequest
from theses import models


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (used by Knox for auth response)"""
    class Meta:
        model = User
        # Only expose these fields via API (security!)
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        # These fields can't be modified via API
        read_only_fields = ('id', 'username')


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model with computed thesis count"""
    # SerializerMethodField: Computed field (read-only)
    # Requires a get_<field_name> method (see below)
    thesis_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            'id', 'first_name', 'last_name', 'email', 'student_id',
            'comments', 'thesis_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_thesis_count(self, obj):
        """
        Calculate value for 'thesis_count' field.

        SerializerMethodField calls this method to get the field value.
        Pattern: get_<field_name>(self, obj)

        Args:
            obj: The Student instance being serialized

        Returns:
            int: Number of theses for this student
        """
        return obj.theses.count()


class StudentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing students"""
    class Meta:
        model = Student
        fields = ('id', 'first_name', 'last_name', 'email', 'student_id')
        read_only_fields = ('id',)


class SupervisorSerializer(serializers.ModelSerializer):
    """Serializer for Supervisor model"""
    thesis_count = serializers.SerializerMethodField()

    class Meta:
        model = Supervisor
        fields = (
            'id', 'first_name', 'last_name', 'email',
            'comments', 'thesis_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_thesis_count(self, obj):
        return obj.supervised_theses.count()


class SupervisorListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing supervisors"""
    class Meta:
        model = Supervisor
        fields = ('id', 'first_name', 'last_name', 'email')
        read_only_fields = ('id',)


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    # source='user.username': Access nested field
    # Follows ForeignKey relationship: comment.user.username
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'thesis', 'user', 'user_name', 'user_full_name',
            'text', 'is_auto_generated', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'is_auto_generated', 'created_at', 'updated_at')

    def get_user_full_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ThesisSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Thesis model with nested relationships.

    Demonstrates NESTED SERIALIZERS - including full related objects
    instead of just IDs.

    Compare:
    - 'students': [1, 2] (just IDs - for writing)
    - 'students_details': [{id: 1, name: "John"}, ...] (full objects - for reading)
    """
    # Nested serializers: Include full student/supervisor objects
    # many=True: There can be multiple students/supervisors
    # read_only=True: Only for output, not input
    students_details = StudentListSerializer(source='students', many=True, read_only=True)
    supervisors_details = SupervisorListSerializer(source='supervisors', many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    # Call model methods to get human-readable choice labels
    # source='get_thesis_type_display': Calls Django's auto-generated method
    thesis_type_display = serializers.CharField(source='get_thesis_type_display', read_only=True)
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)

    class Meta:
        model = Thesis
        fields = (
            'id', 'title', 'thesis_type', 'thesis_type_display',
            'phase', 'phase_display',
            'students', 'students_details',
            'supervisors', 'supervisors_details',
            'date_first_contact', 'date_topic_selected', 'date_registration',
            'date_deadline', 'date_presentation', 'date_review', 'date_final_discussion',
            'git_repository', 'description', 'task_description', 'review',
            'ai_summary_enabled', 'ai_context',
            'comments',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_students(self, value):
        """Ensure at least one student is assigned"""
        if not value:
            raise serializers.ValidationError("At least one student must be assigned to the thesis.")
        return value

    def validate_supervisors(self, value):
        """Ensure at least one supervisor is assigned"""
        if not value:
            raise serializers.ValidationError("At least one supervisor must be assigned to the thesis.")
        return value


class ThesisListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing theses"""
    students_details = StudentListSerializer(source='students', many=True, read_only=True)
    supervisors_details = SupervisorListSerializer(source='supervisors', many=True, read_only=True)
    thesis_type_display = serializers.CharField(source='get_thesis_type_display', read_only=True)
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)

    class Meta:
        model = Thesis
        fields = (
            'id', 'title', 'thesis_type', 'thesis_type_display',
            'phase', 'phase_display',
            'students_details', 'supervisors_details',
            'date_first_contact', 'date_registration', 'date_deadline',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ThesisCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating theses"""

    class Meta:
        model = Thesis
        fields = (
            'id', 'title', 'thesis_type', 'phase',
            'students', 'supervisors',
            'date_first_contact', 'date_topic_selected', 'date_registration',
            'date_deadline', 'date_presentation', 'date_review', 'date_final_discussion',
            'git_repository', 'description', 'task_description', 'review',
            'ai_summary_enabled', 'ai_context',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_students(self, value):
        """Ensure at least one student is assigned"""
        if not value:
            raise serializers.ValidationError("At least one student must be assigned to the thesis.")
        return value

    def validate_supervisors(self, value):
        """Ensure at least one supervisor is assigned"""
        if not value:
            raise serializers.ValidationError("At least one supervisor must be assigned to the thesis.")
        return value


class FeedbackTemplateSerializer(serializers.ModelSerializer):
    """Serializer for feedback templates"""

    class Meta:
        model = models.FeedbackTemplate
        fields = (
            'id', 'name', 'message', 'description',
            'is_active', 'is_write_protected',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_write_protected')


class FeedbackRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating feedback requests via API"""
    message = serializers.CharField(
        help_text="The feedback request message to send to students"
    )

    def create(self, validated_data):
        """Create a feedback request for a thesis"""
        thesis = self.context['thesis']
        user = self.context['request'].user

        # Import here to avoid circular import
        from ..models import Comment, FeedbackRequest

        # Create comment to store the feedback
        comment = Comment.objects.create(
            thesis=thesis,
            user=None,
            text="[Awaiting student feedback]\n\n---\n\n**Request:**\n" + validated_data['message'],
            is_auto_generated=False
        )

        # Create feedback request
        feedback_request = FeedbackRequest.objects.create(
            thesis=thesis,
            comment=comment,
            request_message=validated_data['message'],
            requested_by=user
        )

        return feedback_request


class FeedbackRequestSerializer(serializers.ModelSerializer):
    """Serializer for feedback request details"""
    thesis_id = serializers.IntegerField(source='thesis.id', read_only=True)
    thesis_title = serializers.CharField(source='thesis.title', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    student_url = serializers.SerializerMethodField()

    class Meta:
        model = models.FeedbackRequest
        fields = (
            'id', 'thesis_id', 'thesis_title',
            'request_message', 'is_responded', 'first_response_at',
            'requested_by_name', 'student_url',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_responded', 'first_response_at', 'created_at', 'updated_at')

    def get_requested_by_name(self, obj):
        """Get the name of the user who requested feedback"""
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.username
        return None

    def get_student_url(self, obj):
        """Get the full URL for students to respond"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_student_url())
        return obj.get_student_url()

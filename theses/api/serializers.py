from rest_framework import serializers
from django.contrib.auth.models import User
from theses.models import Student, Supervisor, Thesis, Comment


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (used by Knox)"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id', 'username')


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    thesis_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            'id', 'first_name', 'last_name', 'email', 'student_id',
            'comments', 'thesis_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_thesis_count(self, obj):
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
    """Detailed serializer for Thesis model"""
    students_details = StudentListSerializer(source='students', many=True, read_only=True)
    supervisors_details = SupervisorListSerializer(source='supervisors', many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
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
            'git_repository', 'description', 'comments',
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
            'git_repository', 'description',
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

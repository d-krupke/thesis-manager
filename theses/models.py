"""
MODELS.PY - Database Structure Definitions
==========================================

This file defines the DATABASE SCHEMA - the structure of your database tables.
Each class represents a table, and each field represents a column in that table.

WHAT BELONGS HERE:
------------------
1. Model classes (database tables)
2. Field definitions (columns and their types)
3. Relationships between models (ForeignKey, ManyToMany)
4. Model methods that operate on single instances
5. Properties that compute values from the model's data

HOW TO ADD A NEW FIELD:
-----------------------
1. Add it to the model class:
   new_field = models.CharField(max_length=100, blank=True)

2. Create and run migrations:
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate

COMMON FIELD TYPES:
-------------------
- CharField(max_length=X): Short text (names, titles)
- TextField(): Long text (descriptions, comments)
- EmailField(): Email addresses (validates format)
- URLField(): Web addresses
- DateField(): Dates (YYYY-MM-DD)
- DateTimeField(): Dates with times
- IntegerField(): Whole numbers
- BooleanField(): True/False values
- ForeignKey(): Link to another model (one-to-many)
- ManyToManyField(): Link to multiple instances of another model

COMMON FIELD OPTIONS:
--------------------
- blank=True: Field can be empty in forms
- null=True: Field can be NULL in database
- default='value': Default value if not provided
- unique=True: Value must be unique across all records
- help_text='...': Help text shown in forms/admin
- choices=[...]: List of valid choices for the field

KEY MODEL METHODS:
------------------
- __str__(self): How the object appears as text (required!)
- get_absolute_url(self): Returns URL to view this object
- @property methods: Computed fields that look like attributes
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import secrets


class Student(models.Model):
    """
    Student model - represents a student who can write theses.

    This creates a 'theses_student' table in the database.
    Each instance of this class is one row in that table.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=50, blank=True, null=True)
    comments = models.TextField(blank=True, help_text="Free text comments about the student")
    # auto_now_add=True: Sets timestamp automatically when record is created (never changes)
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now=True: Updates timestamp automatically whenever record is saved
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta class - configuration for this model.

        Common Meta options:
        - ordering: Default order when querying (e.g., ['last_name', 'first_name'])
        - verbose_name: Human-readable singular name
        - verbose_name_plural: Human-readable plural name
        - unique_together: Fields that must be unique together
        """
        ordering = ['last_name', 'first_name']  # Sort by last name, then first name

    def __str__(self):
        """
        String representation - how this object appears as text.

        Used in:
        - Django admin interface
        - Dropdowns and select boxes
        - String conversions (str(student))
        - Debugging output

        Always define this method! Makes your life much easier.
        """
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        """
        Returns the canonical URL for viewing this object.

        The 'reverse' function looks up a URL by its name (from urls.py)
        and fills in any parameters (like 'pk' for primary key).

        Example: reverse('student_detail', kwargs={'pk': 5})
                 returns '/student/5/'
        """
        return reverse('student_detail', kwargs={'pk': self.pk})


class Supervisor(models.Model):
    """
    Supervisor model - represents a thesis supervisor/advisor.

    Supervisors can supervise multiple theses (see ManyToManyField in Thesis model).
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  # unique=True: No two supervisors can have same email
    comments = models.TextField(blank=True, help_text="Free text comments about the supervisor")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('supervisor_detail', kwargs={'pk': self.pk})


class Thesis(models.Model):
    """
    Thesis model - represents a student thesis (bachelor, master, project work).

    This is the central model that connects students and supervisors through
    ManyToMany relationships. It tracks the thesis through all its phases.
    """

    # CHOICES: List of tuples (value_in_db, human_readable_label)
    # Used to create dropdown menus and validate input
    THESIS_TYPES = [
        ('bachelor', 'Bachelor Thesis'),  # Stored as 'bachelor', displayed as 'Bachelor Thesis'
        ('master', 'Master Thesis'),
        ('project', 'Project Work'),
        ('other', 'Other'),
    ]

    PHASES = [
        ('first_contact', 'First Contact'),
        ('topic_discussion', 'Topic Discussion'),
        ('literature_research', 'Literature Research'),
        ('registered', 'Registered'),
        ('working', 'Working'),
        ('submitted', 'Submitted'),
        ('defended', 'Defended'),
        ('reviewed', 'Reviewed'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    # Basic information
    title = models.CharField(max_length=500, blank=True, help_text="Thesis title (can be added later)")
    # choices=THESIS_TYPES: Restricts values to those in THESIS_TYPES list
    thesis_type = models.CharField(max_length=20, choices=THESIS_TYPES, default='bachelor')
    phase = models.CharField(max_length=30, choices=PHASES, default='first_contact')

    # Relationships (the "magic" part of Django!)
    #
    # ManyToManyField creates a relationship where:
    # - One thesis can have multiple students (rare, but possible)
    # - One student can have multiple theses (bachelor, master, etc.)
    # - Django automatically creates a "join table" to manage this relationship
    #
    # related_name='theses': Allows reverse lookup from Student
    #   Example: student.theses.all() gets all theses for a student
    students = models.ManyToManyField(Student, related_name='theses')

    # Same for supervisors - creates many-to-many relationship
    # related_name='supervised_theses': Avoid confusion with 'theses'
    #   Example: supervisor.supervised_theses.all() gets all their theses
    supervisors = models.ManyToManyField(Supervisor, related_name='supervised_theses')

    # Dates
    date_first_contact = models.DateField(null=True, blank=True, help_text="Date of initial contact")
    date_topic_selected = models.DateField(null=True, blank=True, help_text="When topic was finalized")
    date_registration = models.DateField(null=True, blank=True, help_text="Official registration date")
    date_deadline = models.DateField(null=True, blank=True, help_text="Submission deadline")
    date_presentation = models.DateField(null=True, blank=True, help_text="Date of defense/presentation")
    date_review = models.DateField(null=True, blank=True, help_text="Date of review completion")
    date_final_discussion = models.DateField(null=True, blank=True, help_text="Final discussion date")

    # Additional information
    git_repository = models.URLField(blank=True, help_text="URL to student's git repository")
    description = models.TextField(blank=True, help_text="General description of the thesis")
    task_description = models.TextField(blank=True, help_text="Formal multi-paragraph task description defining scope and objectives")
    review = models.TextField(blank=True, help_text="Formal multi-paragraph review of the completed thesis")

    # AI-enhanced reporting settings
    ai_summary_enabled = models.BooleanField(
        default=True,
        help_text="Enable AI-powered progress analysis in weekly reports. "
                  "Disable if student does not consent to external AI processing."
    )
    ai_context = models.TextField(
        blank=True,
        max_length=500,
        help_text="Additional context for AI analysis (max 500 chars). "
                  "E.g., 'Pure theory thesis, no implementation expected' or "
                  "'Focus on hardware development, code changes will be minimal'."
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_first_contact', '-created_at']
        verbose_name_plural = 'Theses'

    def __str__(self):
        if self.title:
            return self.title
        students_str = ", ".join([str(s) for s in self.students.all()[:2]])
        if students_str:
            return f"{self.get_thesis_type_display()} - {students_str}"
        return f"{self.get_thesis_type_display()} (No student assigned)"

    def get_absolute_url(self):
        return reverse('thesis_detail', kwargs={'pk': self.pk})

    @property
    def primary_student(self):
        """
        Property decorator - makes this method look like an attribute.

        Usage: thesis.primary_student (not thesis.primary_student())

        Properties are useful for:
        - Computed fields that don't need to be stored in database
        - Convenience methods that read like attributes
        - Backwards compatibility when refactoring

        Returns the first student (for UI purposes where only one is shown).
        """
        return self.students.first()

    @property
    def primary_supervisor(self):
        """Returns the first supervisor (for UI purposes)"""
        return self.supervisors.first()


class Comment(models.Model):
    """
    Comment model - represents comments on theses.

    Can be manually created by users or auto-generated by signals (see signals.py)
    when dates or phases change.
    """

    # ForeignKey creates a ONE-TO-MANY relationship:
    # - One thesis can have multiple comments
    # - Each comment belongs to exactly one thesis
    #
    # on_delete=models.CASCADE: When thesis is deleted, delete all its comments
    # related_name='comments': Allows reverse lookup
    #   Example: thesis.comments.all() gets all comments for a thesis
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE, related_name='comments')

    # on_delete=models.SET_NULL: When user is deleted, keep comment but set user to NULL
    # null=True: Allow NULL in database (required when using SET_NULL)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    text = models.TextField(help_text="Comment text")
    is_auto_generated = models.BooleanField(default=False, help_text="Was this comment auto-generated?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # '-created_at': The minus sign means descending order (newest first)
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.thesis} at {self.created_at}"


class FeedbackTemplate(models.Model):
    """
    FeedbackTemplate model - stores reusable templates for feedback requests.

    Supervisors can select and customize these templates when requesting
    feedback from students.
    """
    name = models.CharField(max_length=200, help_text="Template name (e.g., 'Weekly Status Update')")
    message = models.TextField(help_text="Template message text (supports Markdown)")
    description = models.TextField(blank=True, help_text="Optional description of when to use this template")
    is_active = models.BooleanField(default=True, help_text="Is this template available for use?")
    is_write_protected = models.BooleanField(default=False, help_text="Prevent users from editing or deleting this template")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class FeedbackRequest(models.Model):
    """
    FeedbackRequest model - tracks feedback requests sent to students.

    When a supervisor requests feedback from students, this creates a special
    comment that students can edit via a secure token link (without login).
    """
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE, related_name='feedback_requests')
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE, related_name='feedback_request')

    # The message/prompt sent to the student
    request_message = models.TextField(help_text="The message/prompt sent to the student")

    # Secure token for student access (no login required)
    token = models.CharField(max_length=64, unique=True, editable=False)

    # Track who requested and when
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='feedback_requests_sent')

    # Track response status
    is_responded = models.BooleanField(default=False, help_text="Has the student responded?")
    first_response_at = models.DateTimeField(null=True, blank=True, help_text="When student first responded")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback request for {self.thesis} by {self.requested_by}"

    def save(self, *args, **kwargs):
        """Generate secure token on creation"""
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def get_student_url(self):
        """Get the public URL for students to respond"""
        return reverse('feedback_respond', kwargs={'token': self.token})

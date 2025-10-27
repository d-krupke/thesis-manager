from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=50, blank=True, null=True)
    comments = models.TextField(blank=True, help_text="Free text comments about the student")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('student_detail', kwargs={'pk': self.pk})


class Supervisor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
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
    THESIS_TYPES = [
        ('bachelor', 'Bachelor Thesis'),
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
    thesis_type = models.CharField(max_length=20, choices=THESIS_TYPES, default='bachelor')
    phase = models.CharField(max_length=30, choices=PHASES, default='first_contact')

    # Relationships
    students = models.ManyToManyField(Student, related_name='theses')
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
        """Returns the first student (for UI purposes)"""
        return self.students.first()

    @property
    def primary_supervisor(self):
        """Returns the first supervisor (for UI purposes)"""
        return self.supervisors.first()


class Comment(models.Model):
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(help_text="Comment text")
    is_auto_generated = models.BooleanField(default=False, help_text="Was this comment auto-generated?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.thesis} at {self.created_at}"

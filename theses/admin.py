"""
ADMIN.PY - Django Admin Interface Configuration
===============================================

This file configures the DJANGO ADMIN interface - a built-in web interface
for managing your database. It's automatically available at /admin/

WHAT BELONGS HERE:
------------------
1. ModelAdmin classes (configure how models appear in admin)
2. Admin customizations (list displays, filters, search)
3. Inline editors (edit related objects on the same page)
4. Custom admin actions
5. Admin-specific methods and properties

WHAT IS DJANGO ADMIN?
---------------------
Django Admin is a powerful built-in interface for:
- Viewing and editing database records
- Searching and filtering data
- Managing users and permissions
- Bulk operations on multiple records

Access it at: http://localhost:8000/admin/
(Requires a superuser account)

MODELADMIN CONFIGURATION:
-------------------------
Common attributes:
- list_display: Which fields to show in the list view
- list_filter: Add filter sidebar for these fields
- search_fields: Enable search box for these fields
- ordering: Default sort order
- readonly_fields: Fields that can't be edited
- fieldsets: Group fields into sections on the edit page
- filter_horizontal: Better widget for ManyToMany fields

REGISTERING MODELS:
-------------------
Two ways to register a model with admin:

1. Decorator (preferred):
   @admin.register(MyModel)
   class MyModelAdmin(admin.ModelAdmin):
       ...

2. Function call:
   admin.site.register(MyModel, MyModelAdmin)

INLINE EDITORS:
---------------
Edit related objects on the same page as the parent:

class MyInline(admin.TabularInline):
    model = RelatedModel
    extra = 1  # Number of empty forms to show

class ParentAdmin(admin.ModelAdmin):
    inlines = [MyInline]

CUSTOM METHODS:
---------------
Add custom columns to list display:

def my_custom_field(self, obj):
    return f"Custom: {obj.name}"
my_custom_field.short_description = 'Column Header'

list_display = ['name', 'my_custom_field']

EXAMPLE:
--------
@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
"""

from django.contrib import admin
from .models import Student, Supervisor, Thesis, Comment, FeedbackTemplate, FeedbackRequest


# @admin.register: Register this model with the admin interface
# This makes Student appear in the admin sidebar
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Student model.

    Customizes how students appear in the Django admin interface.
    """
    # list_display: Columns to show in the list view
    # These fields appear as columns in the table
    list_display = ['last_name', 'first_name', 'email', 'student_id', 'created_at']

    # list_filter: Add filter sidebar for these fields
    # Creates a filter widget on the right side of the page
    list_filter = ['created_at']

    # search_fields: Enable search box for these fields
    # Searches across all listed fields (OR logic)
    search_fields = ['first_name', 'last_name', 'email', 'student_id']

    # ordering: Default sort order for the list view
    ordering = ['last_name', 'first_name']


@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    """
    Admin configuration for Supervisor model.

    Similar to StudentAdmin but for supervisors.
    """
    list_display = ['last_name', 'first_name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['last_name', 'first_name']


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    """
    Admin configuration for Thesis model.

    This is the most complex admin configuration with:
    - Custom display method (title_or_placeholder)
    - Grouped fields (fieldsets)
    - Better widget for ManyToMany (filter_horizontal)
    - Date-based navigation (date_hierarchy)
    """
    # Custom method used in list_display (see below)
    list_display = ['title_or_placeholder', 'thesis_type', 'phase', 'date_first_contact', 'date_registration', 'date_deadline', 'created_at']

    list_filter = ['thesis_type', 'phase', 'date_registration', 'created_at']

    # Search related fields using double underscore
    # 'students__first_name': Search in related Student's first_name
    search_fields = ['title', 'students__first_name', 'students__last_name', 'supervisors__first_name', 'supervisors__last_name']

    # filter_horizontal: Better widget for ManyToMany fields
    # Shows two boxes with arrow buttons to move items between them
    # Much better UX than default multi-select
    filter_horizontal = ['students', 'supervisors']

    # date_hierarchy: Add date-based drill-down navigation at top of page
    # Creates: "2025 › March › 15" breadcrumb navigation
    date_hierarchy = 'date_first_contact'

    ordering = ['-date_first_contact', '-created_at']

    # fieldsets: Group fields into collapsible sections on the edit page
    # Format: (section_name, {options_dict})
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'thesis_type', 'phase')
        }),
        ('People', {
            'fields': ('students', 'supervisors')
        }),
        ('Timeline', {
            'fields': ('date_first_contact', 'date_topic_selected', 'date_registration',
                      'date_deadline', 'date_presentation', 'date_review', 'date_final_discussion')
        }),
        ('Additional Information', {
            'fields': ('git_repository', 'description', 'task_description', 'review')
        }),
        ('AI-Enhanced Reporting Settings', {
            'fields': ('ai_summary_enabled', 'ai_context'),
            'description': 'Configure AI-powered progress analysis for weekly reports. '
                          'Disable if student does not consent to external AI processing.'
        }),
    )

    def title_or_placeholder(self, obj):
        """
        Custom method for list_display.

        Shows thesis title if available, otherwise shows placeholder text.

        Args:
            obj: The Thesis instance

        Returns:
            str: Title or placeholder text
        """
        return obj.title if obj.title else "(No title yet)"

    # short_description: Sets the column header for this custom field
    title_or_placeholder.short_description = 'Title'


# ============================================================================
# INLINE ADMIN: Edit comments within the thesis edit page
# ============================================================================
class CommentInline(admin.TabularInline):
    """
    Inline editor for comments.

    This allows editing comments directly on the thesis edit page,
    without navigating to a separate page.

    TabularInline: Shows data in a table format
    (Alternative: StackedInline shows fields stacked vertically)
    """
    model = Comment

    # extra: Number of empty forms to show for adding new comments
    extra = 0  # Don't show empty forms (can use "Add another Comment" button)

    # fields: Which fields to show in the inline editor
    fields = ['user', 'text', 'is_auto_generated', 'created_at']

    # readonly_fields: These fields can be viewed but not edited
    readonly_fields = ['created_at']

    # can_delete: Allow deleting comments from this inline editor
    can_delete = True


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Comment model.

    Shows comments with a preview of the text (first 50 characters).
    Allows filtering by auto-generated status.
    """
    # Custom method 'text_preview' shows truncated comment text
    list_display = ['thesis', 'user', 'text_preview', 'is_auto_generated', 'created_at']

    list_filter = ['is_auto_generated', 'created_at']

    # Search in related fields: thesis__title, user__username
    search_fields = ['text', 'thesis__title', 'user__username']

    # readonly_fields: Can't be edited (auto-managed by Django)
    readonly_fields = ['created_at', 'updated_at']

    ordering = ['-created_at']

    def text_preview(self, obj):
        """
        Custom method: Show first 50 characters of comment text.

        Truncates long comments for better list display readability.

        Args:
            obj: The Comment instance

        Returns:
            str: Truncated comment text with ellipsis if needed
        """
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Comment'


@admin.register(FeedbackTemplate)
class FeedbackTemplateAdmin(admin.ModelAdmin):
    """
    Admin configuration for FeedbackTemplate model.

    Allows managing reusable templates for feedback requests.
    """
    list_display = ['name', 'is_active', 'is_write_protected', 'created_at', 'updated_at']
    list_filter = ['is_active', 'is_write_protected', 'created_at']
    search_fields = ['name', 'description', 'message']
    ordering = ['name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'is_write_protected')
        }),
        ('Template Content', {
            'fields': ('message', 'description')
        }),
    )


@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for FeedbackRequest model.

    Shows feedback requests with their status and links.
    """
    list_display = ['thesis', 'requested_by', 'is_responded', 'first_response_at', 'created_at']
    list_filter = ['is_responded', 'created_at']
    search_fields = ['thesis__title', 'requested_by__username', 'request_message']
    readonly_fields = ['token', 'created_at', 'updated_at', 'student_link']
    ordering = ['-created_at']

    fieldsets = (
        ('Request Information', {
            'fields': ('thesis', 'requested_by', 'request_message')
        }),
        ('Response Status', {
            'fields': ('is_responded', 'first_response_at', 'comment')
        }),
        ('Access', {
            'fields': ('token', 'student_link'),
            'description': 'Secure token for student access (generated automatically)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_link(self, obj):
        """
        Display the student access URL in the admin interface.
        """
        from django.utils.html import format_html
        url = obj.get_student_url()
        full_url = f"https://example.com{url}"  # Replace with actual domain in production
        return format_html('<a href="{}" target="_blank">{}</a>', full_url, full_url)

    student_link.short_description = 'Student Access Link'

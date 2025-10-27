from django.contrib import admin
from .models import Student, Supervisor, Thesis, Comment


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'email', 'student_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['first_name', 'last_name', 'email', 'student_id']
    ordering = ['last_name', 'first_name']


@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['last_name', 'first_name']


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ['title_or_placeholder', 'thesis_type', 'phase', 'date_first_contact', 'date_registration', 'date_deadline', 'created_at']
    list_filter = ['thesis_type', 'phase', 'date_registration', 'created_at']
    search_fields = ['title', 'students__first_name', 'students__last_name', 'supervisors__first_name', 'supervisors__last_name']
    filter_horizontal = ['students', 'supervisors']
    date_hierarchy = 'date_first_contact'
    ordering = ['-date_first_contact', '-created_at']

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
            'fields': ('git_repository', 'description')
        }),
    )

    def title_or_placeholder(self, obj):
        return obj.title if obj.title else "(No title yet)"
    title_or_placeholder.short_description = 'Title'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ['user', 'text', 'is_auto_generated', 'created_at']
    readonly_fields = ['created_at']
    can_delete = True


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['thesis', 'user', 'text_preview', 'is_auto_generated', 'created_at']
    list_filter = ['is_auto_generated', 'created_at']
    search_fields = ['text', 'thesis__title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Comment'

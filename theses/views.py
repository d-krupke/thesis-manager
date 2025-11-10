"""
VIEWS.PY - Request Handlers and Business Logic
===============================================

This file contains VIEWS - functions or classes that handle HTTP requests
and return HTTP responses. Views sit between URLs (urls.py) and templates.

REQUEST FLOW:
-------------
1. User visits a URL (e.g., /thesis/5/)
2. urls.py maps URL to a view
3. View processes the request (THIS FILE)
4. View returns a rendered template or redirect

WHAT BELONGS HERE:
------------------
1. Class-based views (ListView, DetailView, CreateView, etc.)
2. Function-based views (for simple cases)
3. Business logic (filtering, searching, calculations)
4. Permission checks
5. Context data preparation for templates

CLASS-BASED VIEWS (CBV):
------------------------
Django provides reusable view classes for common patterns:

- ListView: Display a list of objects (e.g., all theses)
- DetailView: Display a single object's details
- CreateView: Form for creating new objects
- UpdateView: Form for editing existing objects
- DeleteView: Confirm and delete objects

KEY METHODS TO OVERRIDE:
------------------------
- get_queryset(self): Customize which objects to fetch from database
- get_context_data(self, **kwargs): Add extra variables to template
- form_valid(self, form): Custom logic when form is submitted successfully
- get_success_url(self): Where to redirect after successful form submission

MIXINS:
-------
- LoginRequiredMixin: Require user to be logged in
- UserPassesTestMixin: Custom permission checks
- Add mixins BEFORE the view class (order matters!)

EXAMPLE:
--------
To add a new list view:

class MyListView(LoginRequiredMixin, ListView):
    model = MyModel
    template_name = 'myapp/my_list.html'
    context_object_name = 'items'
    paginate_by = 50  # Show 50 items per page

    def get_queryset(self):
        # Customize the query
        return MyModel.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        # Add extra context for the template
        context = super().get_context_data(**kwargs)
        context['extra_data'] = 'some value'
        return context
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.db import models
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse
from knox.models import AuthToken
import csv
from .models import Thesis, Student, Supervisor, Comment
from .forms import ThesisForm, StudentForm, SupervisorForm, CommentForm, UserCreationByAdminForm
from .warnings import get_all_thesis_warnings


class ThesisListView(LoginRequiredMixin, ListView):
    """
    List view for displaying all theses with filtering and search.

    Inherits from:
    - LoginRequiredMixin: Requires user to be logged in
    - ListView: Provides list display functionality

    Class attributes configure the view's behavior:
    - model: Which model to query
    - template_name: Which template to render
    - context_object_name: Name of the variable in template (default: 'object_list')
    - paginate_by: Number of items per page (None = no pagination)
    """
    model = Thesis
    template_name = 'theses/thesis_list.html'
    context_object_name = 'theses'
    paginate_by = 50

    def get_queryset(self):
        """
        Customize which objects to display in the list.

        This method is called automatically by ListView. It should return
        a QuerySet (a database query) of objects to display.

        Here we:
        1. Start with all theses
        2. Optimize with prefetch_related (reduces database queries)
        3. Filter based on URL parameters (?phase=registered&search=ml)

        QuerySet methods:
        - filter(): Include only matching objects
        - exclude(): Remove matching objects
        - order_by(): Change sort order
        - prefetch_related(): Efficiently load related objects
        - select_related(): Efficiently load ForeignKey relations

        Returns:
            QuerySet of Thesis objects to display
        """
        # prefetch_related: Loads students and supervisors in separate queries
        # This is MUCH faster than loading them one-by-one for each thesis
        queryset = Thesis.objects.prefetch_related('students', 'supervisors').all()

        # Get URL parameters from the request
        # Example URL: /theses/?phase=registered&phase=working&type=master
        # self.request.GET.getlist('phase') returns ['registered', 'working'] or []
        phases = self.request.GET.getlist('phase')

        if phases:
            # filter(phase__in=phases): Keep only theses with phase in the list
            queryset = queryset.filter(phase__in=phases)
        else:
            # Default: Exclude completed and abandoned phases
            # This keeps the overview focused on active theses
            queryset = queryset.exclude(phase__in=['completed', 'abandoned'])

        thesis_type = self.request.GET.get('type')
        if thesis_type:
            queryset = queryset.filter(thesis_type=thesis_type)

        # Search across multiple fields using Q objects
        # Q objects allow complex queries with OR/AND logic
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                # The pipe (|) means OR
                # __icontains: case-insensitive partial match
                models.Q(title__icontains=search) |
                models.Q(students__first_name__icontains=search) |
                models.Q(students__last_name__icontains=search)
            ).distinct()  # Remove duplicates (needed when filtering on ManyToMany)

        # Handle sorting
        # Get sort field and order from URL parameters (?sort=date_deadline&order=desc)
        sort_by = self.request.GET.get('sort', 'date_first_contact')  # Default sort by first contact date
        order = self.request.GET.get('order', 'asc')  # Default ascending order

        # Define allowed sort fields to prevent SQL injection
        allowed_sort_fields = [
            'title', 'thesis_type', 'phase',
            'date_first_contact', 'date_registration', 'date_deadline',
            'date_presentation', 'date_review', 'date_final_discussion'
        ]

        if sort_by in allowed_sort_fields:
            # Add '-' prefix for descending order
            order_prefix = '-' if order == 'desc' else ''

            # Handle NULL values: put them at the end
            # Use F() expression with nulls_last parameter
            if sort_by.startswith('date_'):
                # For date fields, ensure NULLs go to the end
                queryset = queryset.order_by(
                    F(sort_by).desc(nulls_last=True) if order == 'desc' else F(sort_by).asc(nulls_last=True)
                )
            else:
                # For other fields, use standard ordering
                queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add extra variables to the template context.

        The "context" is a dictionary of variables passed to the template.
        The template can access these as {{ variable_name }}.

        IMPORTANT: Always call super().get_context_data(**kwargs) first!
        This gets the default context (including 'theses' or 'object_list').

        Then add your own variables to the context dictionary.

        Args:
            **kwargs: Keyword arguments (passed automatically, don't worry about it)

        Returns:
            dict: Context dictionary with all variables for the template
        """
        # ALWAYS call super() first to get the base context
        # This includes 'theses' (our context_object_name) and pagination vars
        context = super().get_context_data(**kwargs)

        # Add choices for the filter dropdowns
        # Templates can loop through these: {% for key, label in phases %}
        context['phases'] = Thesis.PHASES
        context['thesis_types'] = Thesis.THESIS_TYPES

        # Remember current filter values (to keep checkboxes/dropdowns selected)
        # .getlist('phase'): Get all 'phase' parameters as a list
        selected_phases = self.request.GET.getlist('phase')
        if not selected_phases:
            # Default: All phases except completed and abandoned
            selected_phases = [p[0] for p in Thesis.PHASES if p[0] not in ['completed', 'abandoned']]
        context['selected_phases'] = selected_phases
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Add sorting parameters for template
        context['current_sort'] = self.request.GET.get('sort', 'date_first_contact')
        context['current_order'] = self.request.GET.get('order', 'asc')

        # Calculate supervisor overview statistics
        # This creates a summary of how many theses each supervisor has in each phase
        supervisors = Supervisor.objects.all()
        supervisor_stats = []

        for supervisor in supervisors:
            stats = {'supervisor': supervisor, 'phases': {}}
            # Count theses per phase for this supervisor
            for phase_key, phase_label in Thesis.PHASES:
                count = Thesis.objects.filter(
                    supervisors=supervisor,  # ManyToMany lookup
                    phase=phase_key
                ).count()
                if count > 0:
                    stats['phases'][phase_label] = count

            # Calculate active thesis count (excluding completed and abandoned)
            active_count = Thesis.objects.filter(
                supervisors=supervisor
            ).exclude(
                phase__in=['completed', 'abandoned']
            ).count()
            stats['active'] = active_count

            # Only include supervisors with active theses
            total = sum(stats['phases'].values())
            if total > 0:
                stats['total'] = total
                supervisor_stats.append(stats)

        context['supervisor_stats'] = supervisor_stats

        # Add workload thresholds and calculate max workload for color scaling
        from django.conf import settings
        context['workload_low_threshold'] = settings.WORKLOAD_LOW_THRESHOLD
        context['workload_medium_threshold'] = settings.WORKLOAD_MEDIUM_THRESHOLD

        # Calculate max active workload for color scaling
        # Use max(any_workload, 6) for adaptive scaling
        max_active = max([stat['active'] for stat in supervisor_stats], default=0)
        context['workload_max'] = max(max_active, 6)

        # Generate warnings for all theses
        # This checks all active theses for conditions that need attention
        # (deadlines, review times, missing data, etc.)
        context['thesis_warnings'] = get_all_thesis_warnings()

        # Now 'supervisor_stats' and 'thesis_warnings' are available in the template
        return context


class ThesisDetailView(LoginRequiredMixin, DetailView):
    model = Thesis
    template_name = 'theses/thesis_detail.html'
    context_object_name = 'thesis'

    def get_queryset(self):
        return Thesis.objects.prefetch_related('students', 'supervisors', 'comments__user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context


class ThesisCreateView(LoginRequiredMixin, CreateView):
    model = Thesis
    form_class = ThesisForm
    template_name = 'theses/thesis_form.html'
    success_url = reverse_lazy('thesis_list')


class ThesisUpdateView(LoginRequiredMixin, UpdateView):
    model = Thesis
    form_class = ThesisForm
    template_name = 'theses/thesis_form.html'

    def form_valid(self, form):
        # Set the current user on the instance for the signal
        form.instance._current_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'theses/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        queryset = Student.objects.annotate(
            thesis_count=models.Count('theses')
        ).order_by('last_name', 'first_name')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(student_id__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'theses/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return Student.objects.prefetch_related('theses__supervisors')


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'theses/student_form.html'
    success_url = reverse_lazy('thesis_list')


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'theses/student_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()


class SupervisorListView(LoginRequiredMixin, ListView):
    model = Supervisor
    template_name = 'theses/supervisor_list.html'
    context_object_name = 'supervisors'
    paginate_by = 50

    def get_queryset(self):
        queryset = Supervisor.objects.annotate(
            thesis_count=models.Count('supervised_theses')
        ).order_by('last_name', 'first_name')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SupervisorDetailView(LoginRequiredMixin, DetailView):
    model = Supervisor
    template_name = 'theses/supervisor_detail.html'
    context_object_name = 'supervisor'

    def get_queryset(self):
        return Supervisor.objects.prefetch_related('supervised_theses__students')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all theses supervised by this supervisor
        theses = self.object.supervised_theses.all()

        # Add statistics by phase
        phase_stats = {}
        for phase_key, phase_label in Thesis.PHASES:
            count = theses.filter(phase=phase_key).count()
            if count > 0:
                phase_stats[phase_label] = count

        context['theses'] = theses
        context['phase_stats'] = phase_stats
        context['total_theses'] = theses.count()

        return context


class SupervisorCreateView(LoginRequiredMixin, CreateView):
    model = Supervisor
    form_class = SupervisorForm
    template_name = 'theses/supervisor_form.html'
    success_url = reverse_lazy('thesis_list')


class SupervisorUpdateView(LoginRequiredMixin, UpdateView):
    model = Supervisor
    form_class = SupervisorForm
    template_name = 'theses/supervisor_form.html'

    def get_success_url(self):
        return reverse_lazy('supervisor_detail', kwargs={'pk': self.object.pk})


# Comment views
@login_required
@require_POST
def add_comment(request, thesis_pk):
    """Add a comment to a thesis"""
    thesis = get_object_or_404(Thesis, pk=thesis_pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.thesis = thesis
        comment.user = request.user
        comment.is_auto_generated = False
        comment.save()
        messages.success(request, 'Comment added successfully.')
    else:
        messages.error(request, 'Error adding comment.')

    return redirect('thesis_detail', pk=thesis_pk)


@login_required
def edit_comment(request, pk):
    """Edit a comment"""
    comment = get_object_or_404(Comment, pk=pk)

    # Only allow editing own comments or if user is staff
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own comments.')
        return redirect('thesis_detail', pk=comment.thesis.pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated successfully.')
            return redirect('thesis_detail', pk=comment.thesis.pk)
    else:
        form = CommentForm(instance=comment)

    context = {
        'form': form,
        'comment': comment,
        'thesis': comment.thesis,
    }
    return render(request, 'theses/comment_edit.html', context)


@login_required
@require_POST
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    thesis_pk = comment.thesis.pk

    # Only allow deleting own comments or if user is staff
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own comments.')
    else:
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')

    return redirect('thesis_detail', pk=thesis_pk)


# API Token Management Views

@login_required
def api_tokens_list(request):
    """List all API tokens for the current user"""
    tokens = AuthToken.objects.filter(user=request.user)
    context = {
        'tokens': tokens,
    }
    return render(request, 'theses/api_tokens.html', context)


@login_required
@require_POST
def api_token_create(request):
    """Create a new API token for the current user"""
    # Check if user has reached the token limit
    token_count = AuthToken.objects.filter(user=request.user).count()
    max_tokens = 10  # Same as in settings

    if token_count >= max_tokens:
        messages.error(request, f'You have reached the maximum number of tokens ({max_tokens}). Please delete an existing token first.')
        return redirect('api_tokens_list')

    # Create the token
    instance, token = AuthToken.objects.create(user=request.user)

    # Store the token in session to display it once
    request.session['new_api_token'] = token
    messages.success(request, 'API token created successfully. Make sure to copy it now - you won\'t be able to see it again!')

    return redirect('api_tokens_list')


@login_required
@require_POST
def api_token_delete(request, token_id):
    """Delete an API token"""
    try:
        # Get the token - Knox stores a hash, so we need to get by primary key
        token = AuthToken.objects.get(pk=token_id, user=request.user)
        token.delete()
        messages.success(request, 'API token deleted successfully.')
    except AuthToken.DoesNotExist:
        messages.error(request, 'Token not found or you don\'t have permission to delete it.')

    return redirect('api_tokens_list')


@login_required
@require_POST
def api_tokens_delete_all(request):
    """Delete all API tokens for the current user"""
    count = AuthToken.objects.filter(user=request.user).delete()[0]
    messages.success(request, f'Deleted {count} API token(s).')
    return redirect('api_tokens_list')


# CSV Export View

@login_required
def export_theses_csv(request):
    """
    Export theses to CSV file with Excel compatibility.

    This view respects all filters and sorting from the thesis list:
    - Phase filters
    - Type filters
    - Search queries
    - Sort order

    The CSV includes UTF-8 BOM for proper Excel compatibility.
    """
    # Reuse the same filtering logic as ThesisListView
    queryset = Thesis.objects.prefetch_related('students', 'supervisors').all()

    # Apply phase filter
    phases = request.GET.getlist('phase')
    if phases:
        queryset = queryset.filter(phase__in=phases)
    else:
        # Default: Exclude completed and abandoned phases
        queryset = queryset.exclude(phase__in=['completed', 'abandoned'])

    # Apply type filter
    thesis_type = request.GET.get('type')
    if thesis_type:
        queryset = queryset.filter(thesis_type=thesis_type)

    # Apply search filter
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            models.Q(title__icontains=search) |
            models.Q(students__first_name__icontains=search) |
            models.Q(students__last_name__icontains=search)
        ).distinct()

    # Apply sorting
    sort_by = request.GET.get('sort', 'date_first_contact')
    order = request.GET.get('order', 'asc')

    allowed_sort_fields = [
        'title', 'thesis_type', 'phase',
        'date_first_contact', 'date_registration', 'date_deadline',
        'date_presentation', 'date_review', 'date_final_discussion'
    ]

    if sort_by in allowed_sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        if sort_by.startswith('date_'):
            queryset = queryset.order_by(
                F(sort_by).desc(nulls_last=True) if order == 'desc' else F(sort_by).asc(nulls_last=True)
            )
        else:
            queryset = queryset.order_by(f'{order_prefix}{sort_by}')

    # Create the HttpResponse with CSV content type and UTF-8 BOM for Excel
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="theses_export.csv"'

    # UTF-8 BOM for Excel compatibility
    response.write('\ufeff')

    writer = csv.writer(response)

    # Write header row
    writer.writerow([
        'Type',
        'Title',
        'Phase',
        'Students',
        'Supervisors',
        'First Contact',
        'Topic Selected',
        'Registration',
        'Deadline',
        'Presentation',
        'Review',
        'Final Discussion',
        'Git Repository',
        'Description',
    ])

    # Write data rows
    for thesis in queryset:
        # Format students as comma-separated names
        students = ', '.join([str(student) for student in thesis.students.all()])

        # Format supervisors as comma-separated names
        supervisors = ', '.join([str(supervisor) for supervisor in thesis.supervisors.all()])

        writer.writerow([
            thesis.get_thesis_type_display(),
            thesis.title or '(No title yet)',
            thesis.get_phase_display(),
            students or '-',
            supervisors or '-',
            thesis.date_first_contact.strftime('%Y-%m-%d') if thesis.date_first_contact else '',
            thesis.date_topic_selected.strftime('%Y-%m-%d') if thesis.date_topic_selected else '',
            thesis.date_registration.strftime('%Y-%m-%d') if thesis.date_registration else '',
            thesis.date_deadline.strftime('%Y-%m-%d') if thesis.date_deadline else '',
            thesis.date_presentation.strftime('%Y-%m-%d') if thesis.date_presentation else '',
            thesis.date_review.strftime('%Y-%m-%d') if thesis.date_review else '',
            thesis.date_final_discussion.strftime('%Y-%m-%d') if thesis.date_final_discussion else '',
            thesis.git_repository or '',
            thesis.description or '',
        ])

    return response


# Admin User Creation View

class AdminCreateUserView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for admin users to create new user accounts.

    This view:
    1. Creates a new user with an unusable password
    2. Sends a password reset email to the new user
    3. Allows the user to set their own password via email link

    This is much more convenient than:
    - Creating user in admin interface
    - Setting a temporary password
    - Opening private tab to trigger "forgot password"
    """
    model = User
    form_class = UserCreationByAdminForm
    template_name = 'theses/user_create_form.html'
    success_url = reverse_lazy('thesis_list')

    def test_func(self):
        """Only allow staff users to access this view"""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Add password reset timeout to context"""
        context = super().get_context_data(**kwargs)
        # Get PASSWORD_RESET_TIMEOUT from settings (default is 3 days = 259200 seconds)
        timeout_seconds = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 259200)
        context['password_reset_timeout_hours'] = timeout_seconds // 3600
        return context

    def form_valid(self, form):
        """
        Save the user and send password reset email.

        This method is called when the form is valid. We:
        1. Create the user with an unusable password (can't login yet)
        2. Generate a password reset token
        3. Send an email with the reset link
        4. Show success message to admin
        """
        # Create the user but don't save yet
        user = form.save(commit=False)
        # Set an unusable password - user must use password reset link
        user.set_unusable_password()
        user.save()

        # Generate password reset token (same as "forgot password" functionality)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Get current site for building the reset URL
        current_site = get_current_site(self.request)
        protocol = 'https' if self.request.is_secure() else 'http'

        # Build the password reset URL
        reset_url = f"{protocol}://{current_site.domain}/accounts/reset/{uid}/{token}/"

        # Prepare email content
        subject = 'Welcome to Thesis Manager - Set Your Password'
        # Get PASSWORD_RESET_TIMEOUT from settings (default is 3 days = 259200 seconds)
        timeout_seconds = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 259200)
        timeout_hours = timeout_seconds // 3600
        context = {
            'user': user,
            'reset_url': reset_url,
            'created_by': self.request.user,
            'password_reset_timeout_hours': timeout_hours,
        }

        # Render plain text version (fallback for email clients that don't support HTML)
        text_message = render_to_string('registration/new_user_email.txt', context)

        # Render HTML version
        try:
            html_message = render_to_string('registration/new_user_email.html', context)
        except:
            # If HTML template fails, just send plain text
            html_message = None

        # Send the email using EmailMultiAlternatives (consistent with signals.py)
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,  # Plain text version (fallback)
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )

            # Attach HTML version if available
            if html_message:
                email.attach_alternative(html_message, "text/html")

            email.send(fail_silently=False)

            messages.success(
                self.request,
                f'User account created successfully for {user.get_full_name()} ({user.username}). '
                f'A password reset email has been sent to {user.email}.'
            )
        except Exception as e:
            # If email fails, still show success but warn about email issue
            messages.warning(
                self.request,
                f'User account created for {user.get_full_name()} ({user.username}), '
                f'but the password reset email could not be sent. Error: {str(e)}'
            )

        return super().form_valid(form)

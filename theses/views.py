from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import models
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from knox.models import AuthToken
from .models import Thesis, Student, Supervisor, Comment
from .forms import ThesisForm, StudentForm, SupervisorForm, CommentForm


class ThesisListView(LoginRequiredMixin, ListView):
    model = Thesis
    template_name = 'theses/thesis_list.html'
    context_object_name = 'theses'
    paginate_by = 50

    def get_queryset(self):
        queryset = Thesis.objects.prefetch_related('students', 'supervisors').all()

        # Filter by phase if specified
        phase = self.request.GET.get('phase')
        if phase:
            queryset = queryset.filter(phase=phase)

        # Filter by thesis type if specified
        thesis_type = self.request.GET.get('type')
        if thesis_type:
            queryset = queryset.filter(thesis_type=thesis_type)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(students__first_name__icontains=search) |
                models.Q(students__last_name__icontains=search)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['phases'] = Thesis.PHASES
        context['thesis_types'] = Thesis.THESIS_TYPES
        context['current_phase'] = self.request.GET.get('phase', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Add supervisor overview
        supervisors = Supervisor.objects.all()
        supervisor_stats = []

        for supervisor in supervisors:
            stats = {'supervisor': supervisor, 'phases': {}}
            for phase_key, phase_label in Thesis.PHASES:
                count = Thesis.objects.filter(
                    supervisors=supervisor,
                    phase=phase_key
                ).count()
                if count > 0:
                    stats['phases'][phase_label] = count

            # Only include supervisors with active theses
            total = sum(stats['phases'].values())
            if total > 0:
                stats['total'] = total
                supervisor_stats.append(stats)

        context['supervisor_stats'] = supervisor_stats
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

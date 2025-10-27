from django import forms
from .models import Thesis, Student, Supervisor, Comment


class ThesisForm(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = [
            'title', 'thesis_type', 'phase',
            'students', 'supervisors',
            'date_first_contact', 'date_topic_selected', 'date_registration',
            'date_deadline', 'date_presentation', 'date_review', 'date_final_discussion',
            'git_repository', 'description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'thesis_type': forms.Select(attrs={'class': 'form-select'}),
            'phase': forms.Select(attrs={'class': 'form-select'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'supervisors': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'date_first_contact': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_topic_selected': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_registration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_presentation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_review': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_final_discussion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'git_repository': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'student_id', 'comments']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class SupervisorForm(forms.ModelForm):
    class Meta:
        model = Supervisor
        fields = ['first_name', 'last_name', 'email', 'comments']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'}),
        }
        labels = {
            'text': '',
        }

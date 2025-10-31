"""
FORMS.PY - Form Definitions
============================

This file defines FORMS - classes that create and validate HTML forms.
Forms handle user input, validation, and saving data to the database.

WHAT BELONGS HERE:
------------------
1. Form classes (especially ModelForm for database models)
2. Field definitions and customizations
3. Validation logic
4. Widget customizations (how form fields look in HTML)

MODELFORM vs FORM:
------------------
- ModelForm: Automatically creates form from a model (most common)
  - Django creates fields based on model fields
  - Handles saving to database automatically
  - Use for create/edit operations

- Form: Custom form not tied to a model
  - Manually define all fields
  - Manually handle data processing
  - Use for search forms, contact forms, etc.

HOW TO ADD A FORM:
------------------
1. Create a ModelForm class
2. Specify the model and fields in Meta class
3. Optionally customize widgets for styling
4. Use in a view (CreateView, UpdateView, or function view)

COMMON WIDGETS:
---------------
- TextInput: Single-line text <input type="text">
- EmailInput: Email field <input type="email">
- URLInput: URL field <input type="url">
- DateInput: Date picker <input type="date">
- Textarea: Multi-line text <textarea>
- Select: Dropdown <select>
- SelectMultiple: Multi-select box
- CheckboxInput: Checkbox <input type="checkbox">

EXAMPLE:
--------
class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = ['field1', 'field2']  # or '__all__' for all fields
        widgets = {
            'field1': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # Custom validation
    def clean_field1(self):
        data = self.cleaned_data['field1']
        if 'bad' in data:
            raise forms.ValidationError("Field1 cannot contain 'bad'")
        return data
"""

from django import forms
from .models import Thesis, Student, Supervisor, Comment


class ThesisForm(forms.ModelForm):
    """
    Form for creating and editing Thesis objects.

    ModelForm automatically:
    - Creates form fields based on model fields
    - Validates data according to model constraints
    - Saves data to database with form.save()
    """

    def __init__(self, *args, **kwargs):
        """
        Override __init__ to make students and supervisors fields optional.

        By default, ManyToMany fields are required in forms.
        We allow creating theses without students/supervisors initially,
        with a warning system to remind users to add them.
        """
        super().__init__(*args, **kwargs)
        self.fields['students'].required = False
        self.fields['supervisors'].required = False

    class Meta:
        """
        Meta class configures the ModelForm.

        - model: Which model this form is for
        - fields: List of fields to include (or use '__all__' for everything)
        - widgets: Customize how fields are rendered in HTML
        - labels: Custom labels for fields (default: field name)
        - help_texts: Custom help text
        - exclude: Fields to exclude (opposite of 'fields')
        """
        model = Thesis
        # Only include these fields in the form (order matters!)
        fields = [
            'title', 'thesis_type', 'phase',
            'students', 'supervisors',
            'date_first_contact', 'date_topic_selected', 'date_registration',
            'date_deadline', 'date_presentation', 'date_review', 'date_final_discussion',
            'git_repository', 'description', 'task_description', 'review',
            'ai_summary_enabled', 'ai_context'
        ]
        # Widgets customize the HTML input elements
        # attrs={'class': 'form-control'}: Adds Bootstrap CSS classes for styling
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'thesis_type': forms.Select(attrs={'class': 'form-select'}),  # Dropdown
            'phase': forms.Select(attrs={'class': 'form-select'}),
            # SelectMultiple: Hold Ctrl/Cmd to select multiple items
            'students': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'supervisors': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            # type='date': Creates HTML5 date picker
            'date_first_contact': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_topic_selected': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_registration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_presentation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_review': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_final_discussion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'git_repository': forms.URLInput(attrs={'class': 'form-control'}),
            # rows=5: Make the textarea 5 rows tall
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            # Larger textareas for multi-paragraph formal documents
            'task_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Formal task description...'}),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Formal thesis review...'}),
            # AI settings
            'ai_summary_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_context': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': '500', 'placeholder': 'E.g., "Pure theory thesis, no implementation expected"'}),
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

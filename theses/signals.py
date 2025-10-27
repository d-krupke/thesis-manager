"""
SIGNALS.PY - Automatic Actions and Event Handlers
==================================================

This file defines SIGNALS - automatic actions that happen when certain events occur.
Think of signals as "hooks" that run code when something happens in your application.

WHAT BELONGS HERE:
------------------
1. Signal receivers (functions decorated with @receiver)
2. Automatic business logic triggered by model changes
3. Side effects that should happen when models are saved/deleted
4. Email notifications
5. Audit logging
6. Cache invalidation

WHAT ARE SIGNALS?
-----------------
Signals are like event listeners. Django emits signals when things happen:
- pre_save: Just BEFORE a model is saved
- post_save: Just AFTER a model is saved
- pre_delete / post_delete: Before/after deletion
- m2m_changed: When ManyToMany relationships change

COMMON SIGNALS:
---------------
- pre_save(sender, instance, **kwargs)
  - Called before saving a model
  - Use to: Validate data, store old values for comparison

- post_save(sender, instance, created, **kwargs)
  - Called after saving a model
  - created: True if new object, False if updating
  - Use to: Send emails, create related objects, update caches

- pre_delete(sender, instance, **kwargs)
  - Called before deleting a model
  - Use to: Create audit logs, prevent deletion

@receiver DECORATOR:
--------------------
@receiver(signal_name, sender=ModelClass)
def my_handler(sender, instance, **kwargs):
    # Do something with instance
    pass

- signal_name: Which signal to listen for (pre_save, post_save, etc.)
- sender: Which model to listen to (only that model triggers this)
- instance: The actual object being saved/deleted

IMPORTANT:
----------
Signals are run synchronously (block the request until done).
For expensive operations, consider:
- Background tasks (Celery)
- Async processing
- fail_silently=True for non-critical operations

WHY USE SIGNALS:
----------------
Good use cases:
- Auto-generating audit logs
- Sending notifications
- Updating denormalized data
- Enforcing business rules

Alternatives to consider:
- Model methods (save(), delete())
- Custom manager methods
- Overriding form.save()

EXAMPLE:
--------
@receiver(post_save, sender=MyModel)
def my_handler(sender, instance, created, **kwargs):
    if created:  # Only for new objects
        # Send welcome email
        send_mail(...)
"""

from django.db.models.signals import pre_save, m2m_changed, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Thesis, Comment


# ============================================================================
# SIGNAL 1: Store original thesis values before saving
# ============================================================================
# This signal runs BEFORE a Thesis is saved to the database.
# It stores the old values so we can detect what changed.
@receiver(pre_save, sender=Thesis)
def store_original_thesis_values(sender, instance, **kwargs):
    """
    Store the original thesis values before saving.

    This is step 1 of the automatic comment generation process.
    We need to know the old values to detect what changed.

    How it works:
    1. Check if this is an existing thesis (has pk) or new (no pk)
    2. If existing, fetch the old version from database
    3. Store it in instance._original for later comparison

    Why this is needed:
    - Django doesn't automatically provide old values
    - We need them to detect changes in the next signal
    """
    # instance.pk exists if this is an update, None if it's new
    if instance.pk:
        try:
            # Fetch the current version from database (before changes)
            # Store as _original attribute (not saved to database)
            instance._original = Thesis.objects.get(pk=instance.pk)
        except Thesis.DoesNotExist:
            # Shouldn't happen, but handle gracefully
            instance._original = None
    else:
        # New thesis - no original to compare against
        instance._original = None


# ============================================================================
# SIGNAL 2: Detect changes and prepare auto-generated comments
# ============================================================================
# This signal also runs BEFORE saving (after signal 1).
# It compares old vs new values and generates comment text.
@receiver(pre_save, sender=Thesis)
def create_comment_on_date_change(sender, instance, **kwargs):
    """
    Detect thesis changes and prepare auto-generated comments.

    This is step 2 of the automatic comment generation process.
    Compares old vs new values and creates comment text for changes.

    Auto-comments are generated for:
    - Date changes (added, removed, or changed)
    - Phase changes (e.g., "First Contact" → "Registered")

    The actual comments are created in post_save (after the thesis is saved).
    We can't create them now because the thesis isn't saved yet.
    """
    # Skip for brand new theses (nothing to compare)
    if not instance.pk:
        return

    # Skip if we don't have original values (shouldn't happen)
    if not hasattr(instance, '_original') or instance._original is None:
        return

    original = instance._original
    changes = []  # Will collect change descriptions

    # Dictionary mapping field names to human-readable labels
    date_fields = {
        'date_first_contact': 'First Contact',
        'date_topic_selected': 'Topic Selected',
        'date_registration': 'Registration',
        'date_deadline': 'Deadline',
        'date_presentation': 'Presentation',
        'date_review': 'Review',
        'date_final_discussion': 'Final Discussion',
    }

    # Check each date field for changes
    for field, label in date_fields.items():
        # getattr(object, 'field_name'): Get the value of a field by name
        old_value = getattr(original, field)
        new_value = getattr(instance, field)

        # Compare old vs new
        if old_value != new_value:
            # Three scenarios:
            if old_value is None and new_value is not None:
                # Date was added
                changes.append(f"{label} date set to {new_value}")
            elif old_value is not None and new_value is None:
                # Date was removed
                changes.append(f"{label} date removed (was {old_value})")
            elif old_value is not None and new_value is not None:
                # Date was changed
                changes.append(f"{label} date changed from {old_value} to {new_value}")

    # Check for phase changes
    if original.phase != instance.phase:
        # Convert phase codes to human-readable labels
        # dict(Thesis.PHASES): Converts [('code', 'Label'), ...] to {'code': 'Label'}
        old_phase = dict(Thesis.PHASES).get(original.phase, original.phase)
        new_phase = dict(Thesis.PHASES).get(instance.phase, instance.phase)
        changes.append(f"Phase changed from '{old_phase}' to '{new_phase}'")

    # Store changes for post_save signal
    # We can't create Comment objects yet because the thesis isn't saved
    if changes:
        instance._pending_changes = changes


# ============================================================================
# SIGNAL 3: Create comments after thesis is saved
# ============================================================================
# This signal runs AFTER the thesis is saved to the database.
# Now we can safely create Comment objects.
@receiver(post_save, sender=Thesis)
def create_comments_after_save(sender, instance, created, **kwargs):
    """
    Create auto-generated comments after thesis is saved.

    This is step 3 (final) of the automatic comment generation process.
    Creates Comment objects for the changes detected in pre_save.

    Args:
        sender: The model class (Thesis)
        instance: The thesis that was just saved
        created: True if new thesis, False if update
        **kwargs: Additional keyword arguments
    """
    # Skip for brand new theses (no changes to comment on)
    if created:
        return

    # Check if there are pending changes from the pre_save signal
    if hasattr(instance, '_pending_changes') and instance._pending_changes:
        # Try to get the user who made the change
        # This is set by the view in views.py (ThesisUpdateView.form_valid)
        user = getattr(instance, '_current_user', None)

        # Create a comment for each change
        for change_text in instance._pending_changes:
            Comment.objects.create(
                thesis=instance,
                user=user,  # May be None for API/admin changes
                text=change_text,
                is_auto_generated=True  # Mark as automatic (not user-written)
            )

        # Clean up: Remove the temporary attribute
        delattr(instance, '_pending_changes')


# ============================================================================
# SIGNAL 4: Send email notifications when comments are created
# ============================================================================
# This signal runs AFTER a Comment is saved to the database.
# It sends email notifications to supervisors about new comments.
@receiver(post_save, sender=Comment)
def send_comment_notification_email(sender, instance, created, **kwargs):
    """
    Send email notifications to supervisors when a comment is added.

    This signal notifies all supervisors of a thesis when:
    - A user adds a manual comment
    - The system auto-generates a comment (date/phase change)

    Email notifications can be disabled in settings.py:
        EMAIL_NOTIFICATIONS_ENABLED = False

    Args:
        sender: The model class (Comment)
        instance: The comment that was just saved
        created: True if new comment, False if update
        **kwargs: Additional keyword arguments
    """
    # Only send for new comments (not updates)
    if not created:
        return

    # Check if email notifications are enabled in settings
    # getattr with default False: Returns False if setting doesn't exist
    if not getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False):
        return

    # Get the thesis and its supervisors
    thesis = instance.thesis
    # Filter to only supervisors with valid email addresses
    # __isnull=False: email field is not NULL
    # .exclude(email=''): email field is not empty string
    supervisors = thesis.supervisors.filter(email__isnull=False).exclude(email='')

    # Skip if no supervisors with email addresses
    if not supervisors.exists():
        return

    # Prepare email content
    # Join all student names with commas
    student_names = ", ".join([str(s) for s in thesis.students.all()])

    # Use thesis title if available, otherwise construct from type and students
    thesis_title = thesis.title or f"{thesis.get_thesis_type_display()} - {student_names}"

    # Get the comment author's name (with fallbacks)
    if instance.user and instance.user.get_full_name():
        comment_author = instance.user.get_full_name()
    elif instance.user:
        comment_author = instance.user.username
    else:
        comment_author = "System"  # Auto-generated without user

    # Label the comment type
    comment_type = "Auto-generated comment" if instance.is_auto_generated else "New comment"

    # Email subject line
    subject = f"[Thesis Manager] {comment_type} on thesis: {thesis_title}"

    # Prepare template context (data passed to email template)
    context = {
        'thesis': thesis,
        'comment': instance,
        'comment_author': comment_author,
        'comment_type': comment_type,
        'student_names': student_names,
        'thesis_title': thesis_title,
    }

    try:
        # Try to render email from template
        # Template: templates/emails/comment_notification.txt
        message = render_to_string('emails/comment_notification.txt', context)
    except:
        # Fallback: Create simple text email if template doesn't exist
        message = f"""
A {comment_type.lower()} has been added to a thesis you are supervising.

Thesis: {thesis_title}
Student(s): {student_names}
Phase: {thesis.get_phase_display()}

Comment by {comment_author}:
{instance.text}

---
This is an automated notification from Thesis Manager.
"""

    # Collect email addresses
    recipient_emails = [supervisor.email for supervisor in supervisors]

    try:
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,  # Must be configured in settings
            recipient_list=recipient_emails,
            fail_silently=True,  # Don't crash if email fails (e.g., SMTP not configured)
        )
    except Exception as e:
        # Log the error but don't crash the application
        # In production, consider using proper logging (logging module)
        print(f"Failed to send email notification: {e}")

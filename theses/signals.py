from django.db.models.signals import pre_save, m2m_changed, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Thesis, Comment


# Store the original values before save
@receiver(pre_save, sender=Thesis)
def store_original_thesis_values(sender, instance, **kwargs):
    """Store original values to detect changes"""
    if instance.pk:
        try:
            instance._original = Thesis.objects.get(pk=instance.pk)
        except Thesis.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(pre_save, sender=Thesis)
def create_comment_on_date_change(sender, instance, **kwargs):
    """Create auto-generated comments when dates are added or changed"""
    if not instance.pk:
        return  # Skip for new instances

    if not hasattr(instance, '_original') or instance._original is None:
        return

    original = instance._original
    changes = []

    # Check each date field
    date_fields = {
        'date_first_contact': 'First Contact',
        'date_topic_selected': 'Topic Selected',
        'date_registration': 'Registration',
        'date_deadline': 'Deadline',
        'date_presentation': 'Presentation',
        'date_review': 'Review',
        'date_final_discussion': 'Final Discussion',
    }

    for field, label in date_fields.items():
        old_value = getattr(original, field)
        new_value = getattr(instance, field)

        if old_value != new_value:
            if old_value is None and new_value is not None:
                changes.append(f"{label} date set to {new_value}")
            elif old_value is not None and new_value is None:
                changes.append(f"{label} date removed (was {old_value})")
            elif old_value is not None and new_value is not None:
                changes.append(f"{label} date changed from {old_value} to {new_value}")

    # Check phase change
    if original.phase != instance.phase:
        old_phase = dict(Thesis.PHASES).get(original.phase, original.phase)
        new_phase = dict(Thesis.PHASES).get(instance.phase, instance.phase)
        changes.append(f"Phase changed from '{old_phase}' to '{new_phase}'")

    # Store changes to be created after save (we need the instance to be saved first)
    if changes:
        instance._pending_changes = changes


@receiver(post_save, sender=Thesis)
def create_comments_after_save(sender, instance, created, **kwargs):
    """Create comments after the thesis is saved"""
    if created:
        return  # Skip for new instances

    if hasattr(instance, '_pending_changes') and instance._pending_changes:
        # Get the user from the current request (if available)
        # This will be set by the view
        user = getattr(instance, '_current_user', None)

        for change_text in instance._pending_changes:
            Comment.objects.create(
                thesis=instance,
                user=user,
                text=change_text,
                is_auto_generated=True
            )

        # Clear pending changes
        delattr(instance, '_pending_changes')


@receiver(post_save, sender=Comment)
def send_comment_notification_email(sender, instance, created, **kwargs):
    """Send email notifications to supervisors when a comment is added"""
    # Only send for new comments
    if not created:
        return

    # Check if email notifications are enabled
    if not getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False):
        return

    # Get the thesis and supervisors
    thesis = instance.thesis
    supervisors = thesis.supervisors.filter(email__isnull=False).exclude(email='')

    if not supervisors.exists():
        return

    # Prepare email data
    student_names = ", ".join([str(s) for s in thesis.students.all()])
    thesis_title = thesis.title or f"{thesis.get_thesis_type_display()} - {student_names}"
    comment_author = instance.user.get_full_name() if instance.user and instance.user.get_full_name() else (instance.user.username if instance.user else "System")
    comment_type = "Auto-generated comment" if instance.is_auto_generated else "New comment"

    # Email subject
    subject = f"[Thesis Manager] {comment_type} on thesis: {thesis_title}"

    # Email body
    context = {
        'thesis': thesis,
        'comment': instance,
        'comment_author': comment_author,
        'comment_type': comment_type,
        'student_names': student_names,
        'thesis_title': thesis_title,
    }

    try:
        # Try to use template if it exists
        message = render_to_string('emails/comment_notification.txt', context)
    except:
        # Fallback to simple text email
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

    # Send email to each supervisor
    recipient_emails = [supervisor.email for supervisor in supervisors]

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=True,  # Don't raise exception if email fails
        )
    except Exception as e:
        # Log the error but don't crash the application
        print(f"Failed to send email notification: {e}")

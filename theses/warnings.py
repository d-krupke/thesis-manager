"""
WARNINGS.PY - Thesis Warning System
====================================

This file contains the logic for generating warnings about theses that need attention.
Warnings are displayed in the thesis overview to alert users about important issues.

WHAT BELONGS HERE:
------------------
1. Warning dataclass definition
2. Urgency level enum
3. Functions that check thesis conditions and generate warnings
4. Warning logic (deadlines, review times, etc.)

HOW TO ADD A NEW WARNING:
-------------------------
1. Add a check in the check_thesis_warnings() function
2. Create the warning with appropriate urgency level
3. The warning will automatically appear in the thesis overview

WARNING URGENCY LEVELS:
-----------------------
- INFO: Informational (blue) - FYI, no action needed yet
- WARNING: Needs attention soon (yellow) - Action should be taken
- URGENT: Needs immediate attention (red) - Overdue or critical

EXAMPLE WARNING CONDITIONS:
---------------------------
- Deadline approaching (within 7 days) → WARNING
- Deadline exceeded → URGENT
- Review not completed within 30 days of submission → WARNING/URGENT
- Thesis stuck in a phase for too long → INFO/WARNING
"""

from dataclasses import dataclass
from enum import Enum
from datetime import date, timedelta
from typing import List, Optional
from .models import Thesis

class WarningUrgency(Enum):
    """
    Enum for warning urgency levels.

    Determines the visual styling of the warning in the UI.
    """
    INFO = "info"        # Blue - informational, no immediate action needed
    WARNING = "warning"  # Yellow - needs attention soon
    URGENT = "urgent"    # Red - needs immediate attention


@dataclass
class ThesisWarning:
    """
    Dataclass representing a warning for a thesis.

    Attributes:
        thesis_id: The ID of the thesis this warning is for
        student_name: Name of the student (for display)
        thesis_title: Title of the thesis (for display)
        message: The warning message to display
        urgency: The urgency level (INFO, WARNING, or URGENT)
    """
    thesis_id: int
    student_name: str
    thesis_title: str
    message: str
    urgency: WarningUrgency

    @property
    def urgency_class(self) -> str:
        """
        Returns the CSS class for this warning's urgency level.

        Used in templates to style the warning appropriately.
        """
        return f"warning-{self.urgency.value}"


def check_thesis_warnings(thesis: Thesis) -> List[ThesisWarning]:
    """
    Check a thesis for warning conditions and return a list of warnings.

    This function examines various aspects of a thesis (dates, phase, etc.)
    and generates warnings for conditions that need attention.

    Args:
        thesis: A Thesis model instance

    Returns:
        List of ThesisWarning objects (may be empty if no warnings)

    Example:
        for thesis in Thesis.objects.all():
            warnings = check_thesis_warnings(thesis)
            for warning in warnings:
                print(f"{warning.urgency}: {warning.message}")
    """
    warnings = []
    today = date.today()

    # Get display names for the warning
    student_name = str(thesis.primary_student) if thesis.primary_student else "Unknown Student"
    thesis_title = thesis.title or f"{thesis.get_thesis_type_display()} (No title)"

    # ========================================================================
    # CHECK 2: Deadline approaching (within 7 days)
    # ========================================================================
    if thesis.date_deadline and thesis.phase not in ['submitted', 'defended', 'reviewed', 'completed']:
        # Only warn if not yet submitted
        days_until_deadline = (thesis.date_deadline - today).days
        if 0 < days_until_deadline <= 7:
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message=f"Deadline in {days_until_deadline} day{'s' if days_until_deadline != 1 else ''}",
                urgency=WarningUrgency.WARNING
            ))

    # ========================================================================
    # CHECK 3: Review overdue (more than 30 days after submission)
    # ========================================================================
    if thesis.phase == 'submitted' and thesis.date_deadline:
        # Thesis is submitted but not yet reviewed
        days_since_submission = (today - thesis.date_deadline).days

        if days_since_submission > 30:
            # Review is severely overdue
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message=f"Review overdue: {days_since_submission} days since submission",
                urgency=WarningUrgency.URGENT
            ))
        elif days_since_submission > 20:
            # Review is approaching the deadline
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message=f"Review needed soon: {days_since_submission} days since submission",
                urgency=WarningUrgency.WARNING
            ))

    # ========================================================================
    # CHECK 4: Presentation date overdue
    # ========================================================================
    if thesis.date_deadline and thesis.date_presentation:
        days_until_deadline = (thesis.date_deadline - today).days
        if days_until_deadline <= 7 and thesis.phase not in ['defended', 'reviewed', 'completed']:
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message="Deadline within 7 days but no presentation date set",
                urgency=WarningUrgency.WARNING
            ))

    # ========================================================================
    # CHECK 5: Registered but no deadline set
    # ========================================================================
    if thesis.phase in ['registered', 'working'] and not thesis.date_deadline:
        warnings.append(ThesisWarning(
            thesis_id=thesis.id,
            student_name=student_name,
            thesis_title=thesis_title,
            message="No deadline set for registered thesis",
            urgency=WarningUrgency.INFO
        ))

    # ========================================================================
    # CHECK 6: Long time in early phases without progress
    # ========================================================================
    if thesis.date_first_contact and thesis.phase in ['first_contact', 'topic_discussion', 'literature_research']:
        last_date = thesis.date_first_contact
        if thesis.date_topic_selected:
            last_date = thesis.date_topic_selected
        days_in_early_phase = (today - last_date).days

        if days_in_early_phase > 90:
            # More than 3 months in early phase
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message=f"In {thesis.get_phase_display()} phase for {days_in_early_phase} days - no registration yet",
                urgency=WarningUrgency.WARNING
            ))
        elif days_in_early_phase > 60:
            # More than 2 months in early phase
            warnings.append(ThesisWarning(
                thesis_id=thesis.id,
                student_name=student_name,
                thesis_title=thesis_title,
                message=f"In {thesis.get_phase_display()} phase for {days_in_early_phase} days",
                urgency=WarningUrgency.INFO
            ))

    # ========================================================================
    # CHECK 7: Missing supervisor or student
    # ========================================================================
    if not thesis.students.exists():
        warnings.append(ThesisWarning(
            thesis_id=thesis.id,
            student_name="No Student",
            thesis_title=thesis_title,
            message="No student assigned to thesis",
            urgency=WarningUrgency.WARNING  # WARNING (yellow) - student can be added later
        ))

    if not thesis.supervisors.exists():
        warnings.append(ThesisWarning(
            thesis_id=thesis.id,
            student_name=student_name,
            thesis_title=thesis_title,
            message="No supervisor assigned to thesis",
            urgency=WarningUrgency.WARNING  # WARNING (yellow) - supervisor can be added later
        ))

    return warnings


def get_all_thesis_warnings() -> List[ThesisWarning]:
    """
    Generate warnings for all theses in the database.

    This function is called by the ThesisListView to display warnings
    in the thesis overview page.

    Returns:
        List of all ThesisWarning objects for all theses

    Note:
        Only generates warnings for non-completed/non-abandoned theses.
        Completed and abandoned theses are excluded to reduce noise.
    """
    

    all_warnings = []

    # Only check theses that are still active
    # Exclude completed and abandoned theses
    active_theses = Thesis.objects.prefetch_related('students', 'supervisors').exclude(
        phase__in=['completed', 'abandoned']
    )

    for thesis in active_theses:
        warnings = check_thesis_warnings(thesis)
        all_warnings.extend(warnings)

    # Sort warnings by urgency (URGENT first, then WARNING, then INFO)
    urgency_order = {
        WarningUrgency.URGENT: 0,
        WarningUrgency.WARNING: 1,
        WarningUrgency.INFO: 2,
    }
    all_warnings.sort(key=lambda w: urgency_order[w.urgency])

    return all_warnings

"""
Pydantic models for CSV import data extraction.

These models define ONLY the essential data that actually goes into the Thesis Manager.
The AI agent will extract these from arbitrary CSV formats.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class StudentInfo(BaseModel):
    """Student information to be created/matched in Thesis Manager."""
    first_name: str = Field(..., description="Student's first name (required)")
    last_name: str = Field(..., description="Student's last name (required)")
    email: Optional[str] = Field(None, description="Student's email address")
    student_id: Optional[str] = Field(None, description="Matriculation/student number")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v and '@' not in v:
            return None
        return v

    def __str__(self):
        parts = [f"{self.first_name} {self.last_name}"]
        if self.email:
            parts.append(f"({self.email})")
        if self.student_id:
            parts.append(f"[ID: {self.student_id}]")
        return " ".join(parts)


class SupervisorInfo(BaseModel):
    """Supervisor information to be created/matched in Thesis Manager."""
    first_name: str = Field(..., description="Supervisor's first name (required)")
    last_name: str = Field(..., description="Supervisor's last name (required)")
    email: Optional[str] = Field(None, description="Supervisor's email address")
    role: Optional[str] = Field(None, description="Role description (stored in comments)")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v and '@' not in v:
            return None
        return v

    def __str__(self):
        parts = [f"{self.first_name} {self.last_name}"]
        if self.email:
            parts.append(f"({self.email})")
        if self.role:
            parts.append(f"[{self.role}]")
        return " ".join(parts)


class ThesisInfo(BaseModel):
    """
    Complete thesis record to be created in Thesis Manager.

    Only includes fields that actually exist in the Thesis model:
    - title, thesis_type, phase
    - students (list), supervisors (list)
    - dates: first_contact, registration, deadline, presentation
    - description, task_description
    """
    # Required
    student: StudentInfo = Field(..., description="Primary student (required)")
    thesis_type: str = Field(..., description="Type: bachelor/master/project/other")

    # Optional thesis fields
    title: Optional[str] = Field(None, description="Thesis title/topic")
    phase: str = Field(default='first_contact', description="Current phase")

    # Supervisors
    supervisors: List[SupervisorInfo] = Field(
        default_factory=list,
        description="List of supervisors"
    )

    # Dates (YYYY-MM-DD format strings)
    date_first_contact: Optional[str] = Field(None, description="First contact date")
    date_registration: Optional[str] = Field(None, description="Official registration date")
    date_deadline: Optional[str] = Field(None, description="Submission deadline")
    date_presentation: Optional[str] = Field(None, description="Defense/presentation date")

    # Descriptions (free text that goes into Thesis model)
    description: Optional[str] = Field(
        None,
        description="General notes/description (can include degree program, semester, grade, etc.)"
    )
    task_description: Optional[str] = Field(None, description="Formal task description if available")

    # Metadata for user feedback
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about data quality or parsing issues"
    )

    @field_validator('thesis_type')
    @classmethod
    def normalize_thesis_type(cls, v):
        """Normalize thesis type to valid values."""
        if not v:
            return 'other'

        v_clean = v.lower().strip()

        # Map common variations
        if v_clean in ['b', 'bachelor', 'bachelorarbeit', 'ba', 'bsc']:
            return 'bachelor'
        elif v_clean in ['m', 'master', 'masterarbeit', 'ma', 'msc']:
            return 'master'
        elif v_clean in ['p', 'project', 'projektarbeit', 'proj']:
            return 'project'
        else:
            return 'other'

    @field_validator('phase')
    @classmethod
    def normalize_phase(cls, v):
        """Normalize phase to valid values."""
        if not v:
            return 'first_contact'

        v_clean = v.lower().strip()

        # Direct matches
        valid_phases = [
            'first_contact', 'topic_discussion', 'literature_research',
            'registered', 'working', 'submitted', 'defended', 'reviewed',
            'completed', 'abandoned'
        ]

        if v_clean in valid_phases:
            return v_clean

        # Keyword-based inference
        if any(kw in v_clean for kw in ['abandon', 'abbruch', 'cancelled']):
            return 'abandoned'
        elif any(kw in v_clean for kw in ['complete', 'done', 'fertig', 'finished']):
            return 'completed'
        elif any(kw in v_clean for kw in ['review', 'begutacht', 'graded']):
            return 'reviewed'
        elif any(kw in v_clean for kw in ['defend', 'vortrag', 'present', 'kolloquium']):
            return 'defended'
        elif any(kw in v_clean for kw in ['submit', 'abgegeben', 'abgabe']):
            return 'submitted'
        elif any(kw in v_clean for kw in ['work', 'writing', 'arbeit']):
            return 'working'
        elif any(kw in v_clean for kw in ['register', 'anmeld']):
            return 'registered'
        elif any(kw in v_clean for kw in ['research', 'recherch', 'literature']):
            return 'literature_research'
        elif any(kw in v_clean for kw in ['topic', 'thema']):
            return 'topic_discussion'

        return 'first_contact'

    def __str__(self):
        lines = [f"[{self.thesis_type}] {self.title or 'Untitled'}"]
        lines.append(f"  Student: {self.student}")
        if self.supervisors:
            lines.append(f"  Supervisors: {', '.join(str(s) for s in self.supervisors)}")
        else:
            lines.append("  Supervisors: None")
        lines.append(f"  Phase: {self.phase}")

        # Show dates if present
        dates = []
        if self.date_first_contact:
            dates.append(f"First contact: {self.date_first_contact}")
        if self.date_registration:
            dates.append(f"Registration: {self.date_registration}")
        if self.date_deadline:
            dates.append(f"Deadline: {self.date_deadline}")
        if self.date_presentation:
            dates.append(f"Presentation: {self.date_presentation}")

        if dates:
            lines.append(f"  Dates: {', '.join(dates)}")

        if self.warnings:
            lines.append(f"  ⚠ Warnings: {'; '.join(self.warnings)}")

        return "\n".join(lines)

"""
Pydantic models for CSV import data extraction.

These models define the structure of data that can be extracted from CSV rows
for importing into the Thesis Manager system.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import date


class StudentInfo(BaseModel):
    """
    Student information extracted from a CSV row.
    """
    first_name: str = Field(..., description="Student's first name")
    last_name: str = Field(..., description="Student's last name")
    email: Optional[str] = Field(None, description="Student's email address")
    student_id: Optional[str] = Field(None, description="Matriculation number or student ID")
    additional_notes: Optional[str] = Field(None, description="Any additional notes about the student from the CSV")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v and '@' not in v:
            # Return None for invalid emails rather than raising error
            return None
        return v

    def __str__(self):
        result = f"{self.first_name} {self.last_name}"
        if self.email:
            result += f" ({self.email})"
        if self.student_id:
            result += f" [ID: {self.student_id}]"
        return result


class SupervisorInfo(BaseModel):
    """
    Supervisor information extracted from a CSV row.
    """
    first_name: str = Field(..., description="Supervisor's first name")
    last_name: str = Field(..., description="Supervisor's last name")
    email: Optional[str] = Field(None, description="Supervisor's email address")
    role: Optional[str] = Field(None, description="Role (e.g., 'primary supervisor', 'second reviewer')")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v and '@' not in v:
            return None
        return v

    def __str__(self):
        result = f"{self.first_name} {self.last_name}"
        if self.email:
            result += f" ({self.email})"
        if self.role:
            result += f" [{self.role}]"
        return result


class ThesisInfo(BaseModel):
    """
    Complete thesis information extracted from a CSV row.
    """
    # Student information
    student: StudentInfo = Field(..., description="Student information")

    # Supervisor information
    supervisors: List[SupervisorInfo] = Field(
        default_factory=list,
        description="List of supervisors (can be empty if not specified)"
    )

    # Thesis details
    thesis_type: str = Field(..., description="Type: 'bachelor', 'master', 'project', or 'other'")
    title: Optional[str] = Field(None, description="Thesis title/topic")
    phase: str = Field(
        default='first_contact',
        description="Current phase of the thesis"
    )

    # Dates (as strings in YYYY-MM-DD format or None)
    date_first_contact: Optional[str] = Field(None, description="First contact date (YYYY-MM-DD)")
    date_registration: Optional[str] = Field(None, description="Registration date (YYYY-MM-DD)")
    date_deadline: Optional[str] = Field(None, description="Submission deadline (YYYY-MM-DD)")
    date_presentation: Optional[str] = Field(None, description="Presentation date (YYYY-MM-DD)")
    date_submission: Optional[str] = Field(None, description="Actual submission date (YYYY-MM-DD)")

    # Additional information
    description: Optional[str] = Field(None, description="General description or notes")
    task_description: Optional[str] = Field(None, description="Formal task description")
    degree_program: Optional[str] = Field(None, description="Student's degree program (Studiengang)")
    semester_count: Optional[str] = Field(None, description="Number of semesters")
    grade: Optional[str] = Field(None, description="Final grade")

    # Data quality
    is_complete: bool = Field(
        default=True,
        description="Whether the data appears complete (False if critical info missing)"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of important missing fields"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings about the data quality"
    )

    @field_validator('thesis_type')
    @classmethod
    def validate_thesis_type(cls, v):
        """Normalize thesis type to expected values."""
        v_lower = v.lower().strip()

        # Map common variations
        mapping = {
            'b': 'bachelor',
            'bachelor': 'bachelor',
            'bachelorarbeit': 'bachelor',
            'm': 'master',
            'master': 'master',
            'masterarbeit': 'master',
            'p': 'project',
            'project': 'project',
            'projektarbeit': 'project',
        }

        return mapping.get(v_lower, 'other')

    @field_validator('phase')
    @classmethod
    def validate_phase(cls, v):
        """Normalize phase to expected values."""
        if not v:
            return 'first_contact'

        v_lower = v.lower().strip()

        # Map common variations
        valid_phases = [
            'first_contact', 'topic_discussion', 'literature_research',
            'registered', 'working', 'submitted', 'defended', 'reviewed',
            'completed', 'abandoned'
        ]

        if v_lower in valid_phases:
            return v_lower

        # Try to infer phase from keywords
        if 'abandon' in v_lower or 'abbruch' in v_lower:
            return 'abandoned'
        elif 'complete' in v_lower or 'fertig' in v_lower:
            return 'completed'
        elif 'review' in v_lower or 'begutacht' in v_lower:
            return 'reviewed'
        elif 'defend' in v_lower or 'vortrag' in v_lower or 'präsent' in v_lower:
            return 'defended'
        elif 'submit' in v_lower or 'abgabe' in v_lower or 'abgegeben' in v_lower:
            return 'submitted'
        elif 'work' in v_lower or 'arbeit' in v_lower:
            return 'working'
        elif 'register' in v_lower or 'anmeld' in v_lower:
            return 'registered'
        elif 'research' in v_lower or 'recherch' in v_lower:
            return 'literature_research'
        elif 'topic' in v_lower or 'thema' in v_lower:
            return 'topic_discussion'

        return 'first_contact'

    def __str__(self):
        result = f"[{self.thesis_type}] {self.title or 'Untitled'}\n"
        result += f"  Student: {self.student}\n"
        if self.supervisors:
            result += f"  Supervisors: {', '.join(str(s) for s in self.supervisors)}\n"
        result += f"  Phase: {self.phase}"
        if self.missing_fields:
            result += f"\n  Missing: {', '.join(self.missing_fields)}"
        if self.warnings:
            result += f"\n  Warnings: {', '.join(self.warnings)}"
        return result


class CSVRowData(BaseModel):
    """
    Raw data from a single CSV row (German thesis data format).

    This represents the actual columns in the CSV file.
    """
    row_index: int = Field(..., description="Row number in the CSV file")
    name: Optional[str] = Field(None, description="Name (last name)")
    vorname: Optional[str] = Field(None, description="Vorname (first name)")
    email: Optional[str] = Field(None, description="Email-Adresse")
    anmeldung_datum: Optional[str] = Field(None, description="Anmeldung Datum (registration date)")
    abgabe_datum: Optional[str] = Field(None, description="Abgabe Datum (submission deadline)")
    studiengang: Optional[str] = Field(None, description="Studiengang (degree program)")
    semesterzahl: Optional[str] = Field(None, description="Semesterzahl (semester count)")
    alg_veranstaltungen: Optional[str] = Field(None, description="ALG-Veranstaltungen")
    thesis_type: Optional[str] = Field(None, description="B/M/P (Bachelor/Master/Project)")
    matr_nr: Optional[str] = Field(None, description="Matr. Nr. (matriculation number)")
    erstkontakt: Optional[str] = Field(None, description="Erstkontakt (first contact)")
    aufgabenstellung_betreuer: Optional[str] = Field(None, description="Aufgabenst. u. Betreuer")
    thema: Optional[str] = Field(None, description="Thema (topic)")
    noten: Optional[str] = Field(None, description="Noten (notes/grades)")
    literatur_recherche: Optional[str] = Field(None, description="Literatur-Recherche")
    abgegeben_am: Optional[str] = Field(None, description="abgegeben am (submitted on)")
    vortrag_am: Optional[str] = Field(None, description="Vortrag am (presentation on)")
    betreuer_wma: Optional[str] = Field(None, description="Betreuer WMA")
    zweitgutachter: Optional[str] = Field(None, description="Zweitgutachter (second reviewer)")
    note: Optional[str] = Field(None, description="Note (grade)")
    beschreibung: Optional[str] = Field(None, description="Besch. 4,0 + Vortr.")

    def __str__(self):
        return f"Row {self.row_index}: {self.vorname} {self.name} - {self.thema or 'No topic'}"

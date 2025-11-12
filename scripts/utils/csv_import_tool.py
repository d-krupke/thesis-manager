"""
CSV Import Tool for Thesis Manager.

This module provides a tool class that can be used by PydanticAI agents
to import thesis data from CSV files into the Thesis Manager system.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .thesis_manager_client import ThesisManagerClient
from .matching import (
    match_student,
    match_supervisor,
    match_thesis,
    format_person_display,
    format_thesis_display
)
from .csv_import_models import StudentInfo, SupervisorInfo, ThesisInfo

logger = logging.getLogger(__name__)


class CSVImportTool:
    """
    Tool for importing thesis data from CSV files.

    This class provides methods that can be called by PydanticAI agents
    to perform the import process step by step.
    """

    def __init__(self, client: ThesisManagerClient):
        """
        Initialize the import tool.

        Args:
            client: ThesisManagerClient instance for API access
        """
        self.client = client
        self._cached_students: Optional[List[Dict[str, Any]]] = None
        self._cached_supervisors: Optional[List[Dict[str, Any]]] = None
        self._cached_theses: Optional[List[Dict[str, Any]]] = None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """
        Get all students from the system (cached).

        Returns:
            List of student dictionaries
        """
        if self._cached_students is None:
            logger.info("Fetching all students from API...")
            self._cached_students = self.client.list_students()
            logger.info("Cached %d students", len(self._cached_students))
        return self._cached_students

    def get_all_supervisors(self) -> List[Dict[str, Any]]:
        """
        Get all supervisors from the system (cached).

        Returns:
            List of supervisor dictionaries
        """
        if self._cached_supervisors is None:
            logger.info("Fetching all supervisors from API...")
            self._cached_supervisors = self.client.list_supervisors()
            logger.info("Cached %d supervisors", len(self._cached_supervisors))
        return self._cached_supervisors

    def get_all_theses(self) -> List[Dict[str, Any]]:
        """
        Get all theses from the system (cached, without heavy fields).

        Returns:
            List of thesis dictionaries
        """
        if self._cached_theses is None:
            logger.info("Fetching all theses from API...")
            self._cached_theses = self.client.list_theses()
            logger.info("Cached %d theses", len(self._cached_theses))
        return self._cached_theses

    def clear_cache(self):
        """Clear all cached data to force refresh."""
        self._cached_students = None
        self._cached_supervisors = None
        self._cached_theses = None
        logger.info("Cleared all caches")

    def find_or_suggest_student(
        self,
        student_info: StudentInfo,
        threshold: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], List[Tuple[Dict[str, Any], float]]]:
        """
        Find existing student or suggest matches.

        Args:
            student_info: Student information to search for
            threshold: Minimum similarity threshold for matches

        Returns:
            Tuple of (exact_match, suggested_matches)
            - exact_match: Student dict if found with 100% certainty, None otherwise
            - suggested_matches: List of (student, score) tuples for similar matches
        """
        all_students = self.get_all_students()

        matches = match_student(
            first_name=student_info.first_name,
            last_name=student_info.last_name,
            email=student_info.email,
            student_id=student_info.student_id,
            students=all_students,
            threshold=threshold
        )

        # If we have a perfect match (1.0), consider it exact
        if matches and matches[0][1] >= 0.99:
            return matches[0][0], matches

        return None, matches

    def find_or_suggest_supervisor(
        self,
        supervisor_info: SupervisorInfo,
        threshold: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], List[Tuple[Dict[str, Any], float]]]:
        """
        Find existing supervisor or suggest matches.

        Args:
            supervisor_info: Supervisor information to search for
            threshold: Minimum similarity threshold for matches

        Returns:
            Tuple of (exact_match, suggested_matches)
        """
        all_supervisors = self.get_all_supervisors()

        matches = match_supervisor(
            first_name=supervisor_info.first_name,
            last_name=supervisor_info.last_name,
            email=supervisor_info.email,
            supervisors=all_supervisors,
            threshold=threshold
        )

        # If we have a perfect match (1.0), consider it exact
        if matches and matches[0][1] >= 0.99:
            return matches[0][0], matches

        return None, matches

    def find_similar_theses(
        self,
        thesis_info: ThesisInfo,
        student_ids: List[int],
        threshold: float = 0.7
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        """
        Find similar existing theses.

        Args:
            thesis_info: Thesis information to search for
            student_ids: List of student IDs for the thesis
            threshold: Minimum similarity threshold

        Returns:
            List of (thesis, score, reason) tuples
        """
        all_theses = self.get_all_theses()

        matches = match_thesis(
            thesis_type=thesis_info.thesis_type,
            title=thesis_info.title,
            student_ids=student_ids,
            theses=all_theses,
            title_threshold=threshold
        )

        return matches

    def create_student(self, student_info: StudentInfo) -> Optional[Dict[str, Any]]:
        """
        Create a new student.

        Args:
            student_info: Student information

        Returns:
            Created student dictionary or None if failed
        """
        # Generate a placeholder email if none provided
        email = student_info.email
        if not email:
            # Use a placeholder email based on name
            email = f"{student_info.first_name.lower()}.{student_info.last_name.lower()}@example.com"
            logger.warning("No email provided for student, using placeholder: %s", email)

        result = self.client.create_student(
            first_name=student_info.first_name,
            last_name=student_info.last_name,
            email=email,
            student_id=student_info.student_id,
            comments=student_info.additional_notes
        )

        if result:
            # Update cache
            if self._cached_students is not None:
                self._cached_students.append(result)

        return result

    def create_supervisor(self, supervisor_info: SupervisorInfo) -> Optional[Dict[str, Any]]:
        """
        Create a new supervisor.

        Args:
            supervisor_info: Supervisor information

        Returns:
            Created supervisor dictionary or None if failed
        """
        # Generate a placeholder email if none provided
        email = supervisor_info.email
        if not email:
            email = f"{supervisor_info.first_name.lower()}.{supervisor_info.last_name.lower()}@example.com"
            logger.warning("No email provided for supervisor, using placeholder: %s", email)

        comments = None
        if supervisor_info.role:
            comments = f"Role: {supervisor_info.role}"

        result = self.client.create_supervisor(
            first_name=supervisor_info.first_name,
            last_name=supervisor_info.last_name,
            email=email,
            comments=comments
        )

        if result:
            # Update cache
            if self._cached_supervisors is not None:
                self._cached_supervisors.append(result)

        return result

    def create_thesis(
        self,
        thesis_info: ThesisInfo,
        student_ids: List[int],
        supervisor_ids: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new thesis.

        Args:
            thesis_info: Thesis information
            student_ids: List of student IDs
            supervisor_ids: List of supervisor IDs

        Returns:
            Created thesis dictionary or None if failed
        """
        # Build description from various fields
        description_parts = []

        if thesis_info.degree_program:
            description_parts.append(f"Degree Program: {thesis_info.degree_program}")

        if thesis_info.semester_count:
            description_parts.append(f"Semester: {thesis_info.semester_count}")

        if thesis_info.description:
            description_parts.append(f"\nNotes: {thesis_info.description}")

        if thesis_info.grade:
            description_parts.append(f"\nGrade: {thesis_info.grade}")

        description = "\n".join(description_parts) if description_parts else None

        result = self.client.create_thesis(
            thesis_type=thesis_info.thesis_type,
            student_ids=student_ids,
            supervisor_ids=supervisor_ids,
            title=thesis_info.title or "Untitled",
            phase=thesis_info.phase,
            date_first_contact=thesis_info.date_first_contact,
            date_registration=thesis_info.date_registration,
            date_deadline=thesis_info.date_deadline,
            date_presentation=thesis_info.date_presentation,
            description=description,
            task_description=thesis_info.task_description
        )

        if result:
            # Update cache
            if self._cached_theses is not None:
                self._cached_theses.append(result)

        return result

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse various date formats and return YYYY-MM-DD format.

        Args:
            date_str: Date string in various formats

        Returns:
            Date in YYYY-MM-DD format or None if parsing fails
        """
        if not date_str or not date_str.strip():
            return None

        date_str = date_str.strip()

        # Common formats to try
        formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%d.%m.%Y',      # 15.01.2024
            '%d.%m.%y',      # 15.01.24
            '%d/%m/%Y',      # 15/01/2024
            '%d/%m/%y',      # 15/01/24
            '%Y/%m/%d',      # 2024/01/15
            '%d-%m-%Y',      # 15-01-2024
            '%d-%m-%y',      # 15-01-24
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        logger.warning("Could not parse date: %s", date_str)
        return None

    def format_import_summary(
        self,
        thesis_info: ThesisInfo,
        student_match: Optional[Dict[str, Any]],
        student_suggestions: List[Tuple[Dict[str, Any], float]],
        supervisor_matches: List[Optional[Dict[str, Any]]],
        supervisor_suggestions: List[List[Tuple[Dict[str, Any], float]]],
        thesis_matches: List[Tuple[Dict[str, Any], float, str]]
    ) -> str:
        """
        Format a summary of the import operation for user review.

        Args:
            thesis_info: Thesis information to import
            student_match: Exact student match or None
            student_suggestions: List of suggested student matches
            supervisor_matches: List of exact supervisor matches or None
            supervisor_suggestions: List of suggested matches for each supervisor
            thesis_matches: List of similar existing theses

        Returns:
            Formatted string summary
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"IMPORT SUMMARY: {thesis_info.title or 'Untitled'}")
        lines.append("=" * 80)
        lines.append("")

        # Student section
        lines.append("STUDENT:")
        lines.append(f"  {thesis_info.student}")
        if student_match:
            lines.append(f"  ✓ Found existing: {student_match['first_name']} {student_match['last_name']} (ID: {student_match['id']})")
        elif student_suggestions:
            lines.append("  ? Possible matches found:")
            for match, score in student_suggestions[:3]:
                lines.append(format_person_display(match, score))
            lines.append("  → Will need to confirm: use existing or create new")
        else:
            lines.append("  ✗ Not found - will create new student")

        lines.append("")

        # Supervisors section
        if thesis_info.supervisors:
            lines.append("SUPERVISORS:")
            for i, sup_info in enumerate(thesis_info.supervisors):
                lines.append(f"  {i+1}. {sup_info}")
                sup_match = supervisor_matches[i] if i < len(supervisor_matches) else None
                sup_suggestions = supervisor_suggestions[i] if i < len(supervisor_suggestions) else []

                if sup_match:
                    lines.append(f"     ✓ Found existing: {sup_match['first_name']} {sup_match['last_name']} (ID: {sup_match['id']})")
                elif sup_suggestions:
                    lines.append("     ? Possible matches found:")
                    for match, score in sup_suggestions[:3]:
                        lines.append("   " + format_person_display(match, score))
                    lines.append("     → Will need to confirm: use existing or create new")
                else:
                    lines.append("     ✗ Not found - will create new supervisor")
        else:
            lines.append("SUPERVISORS: None specified")

        lines.append("")

        # Thesis section
        lines.append("THESIS:")
        lines.append(f"  Type: {thesis_info.thesis_type}")
        lines.append(f"  Title: {thesis_info.title or 'Untitled'}")
        lines.append(f"  Phase: {thesis_info.phase}")
        if thesis_info.date_first_contact:
            lines.append(f"  First Contact: {thesis_info.date_first_contact}")
        if thesis_info.date_registration:
            lines.append(f"  Registration: {thesis_info.date_registration}")
        if thesis_info.date_deadline:
            lines.append(f"  Deadline: {thesis_info.date_deadline}")

        if thesis_matches:
            lines.append("")
            lines.append("  ⚠ WARNING: Similar theses found in database:")
            for thesis, score, reason in thesis_matches[:3]:
                lines.append(format_thesis_display(thesis, score, reason))
            lines.append("  → This might be a duplicate!")
        else:
            lines.append("  ✓ No similar theses found - appears to be new")

        if thesis_info.warnings:
            lines.append("")
            lines.append("  ⚠ DATA WARNINGS:")
            for warning in thesis_info.warnings:
                lines.append(f"    - {warning}")

        if thesis_info.missing_fields:
            lines.append("")
            lines.append("  ℹ Missing fields: " + ", ".join(thesis_info.missing_fields))

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

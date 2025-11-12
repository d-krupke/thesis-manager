"""
Fuzzy matching utilities for finding similar records in the Thesis Manager.

This module provides utilities for matching students, supervisors, and theses
using fuzzy string matching techniques to handle non-uniform data.
"""

from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher


def normalize_string(s: Optional[str]) -> str:
    """
    Normalize a string for comparison by converting to lowercase and stripping whitespace.

    Args:
        s: String to normalize

    Returns:
        Normalized string
    """
    if not s:
        return ""
    return s.lower().strip()


def similarity_ratio(s1: Optional[str], s2: Optional[str]) -> float:
    """
    Calculate similarity ratio between two strings (0.0 to 1.0).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity ratio (0.0 = completely different, 1.0 = identical)
    """
    s1_norm = normalize_string(s1)
    s2_norm = normalize_string(s2)

    if not s1_norm or not s2_norm:
        return 0.0

    return SequenceMatcher(None, s1_norm, s2_norm).ratio()


def match_person(
    first_name: Optional[str],
    last_name: Optional[str],
    email: Optional[str],
    candidates: List[Dict[str, Any]],
    threshold: float = 0.8
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Find matching persons (students or supervisors) from a list of candidates.

    Uses fuzzy matching on names and exact matching on email.

    Args:
        first_name: First name to match
        last_name: Last name to match
        email: Email to match (exact match has highest priority)
        candidates: List of person dictionaries to match against
        threshold: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of tuples (candidate, similarity_score) sorted by score (highest first)
    """
    matches = []

    for candidate in candidates:
        scores = []

        # Email gets highest priority - exact match means definite match
        if email and candidate.get('email'):
            if normalize_string(email) == normalize_string(candidate['email']):
                return [(candidate, 1.0)]  # Perfect match, return immediately

        # Calculate name similarities
        if first_name and candidate.get('first_name'):
            first_name_sim = similarity_ratio(first_name, candidate['first_name'])
            scores.append(first_name_sim)

        if last_name and candidate.get('last_name'):
            last_name_sim = similarity_ratio(last_name, candidate['last_name'])
            scores.append(last_name_sim)

        # Calculate overall score (average of available scores)
        if scores:
            overall_score = sum(scores) / len(scores)
            if overall_score >= threshold:
                matches.append((candidate, overall_score))

    # Sort by score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def match_student(
    first_name: Optional[str],
    last_name: Optional[str],
    email: Optional[str],
    student_id: Optional[str],
    students: List[Dict[str, Any]],
    threshold: float = 0.8
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Find matching students from a list of candidates.

    Args:
        first_name: Student's first name
        last_name: Student's last name
        email: Student's email
        student_id: Student's matriculation number
        students: List of student dictionaries
        threshold: Minimum similarity threshold

    Returns:
        List of tuples (student, similarity_score) sorted by score
    """
    # Check for exact student_id match first
    if student_id:
        for student in students:
            if student.get('student_id') and normalize_string(student_id) == normalize_string(student['student_id']):
                return [(student, 1.0)]

    # Fall back to name/email matching
    return match_person(first_name, last_name, email, students, threshold)


def match_supervisor(
    first_name: Optional[str],
    last_name: Optional[str],
    email: Optional[str],
    supervisors: List[Dict[str, Any]],
    threshold: float = 0.8
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Find matching supervisors from a list of candidates.

    Args:
        first_name: Supervisor's first name
        last_name: Supervisor's last name
        email: Supervisor's email
        supervisors: List of supervisor dictionaries
        threshold: Minimum similarity threshold

    Returns:
        List of tuples (supervisor, similarity_score) sorted by score
    """
    return match_person(first_name, last_name, email, supervisors, threshold)


def match_thesis(
    thesis_type: Optional[str],
    title: Optional[str],
    student_ids: List[int],
    theses: List[Dict[str, Any]],
    title_threshold: float = 0.6
) -> List[Tuple[Dict[str, Any], float, str]]:
    """
    Find matching theses from a list of candidates.

    Matches primarily on thesis_type + student, with optional title similarity.

    Args:
        thesis_type: Type of thesis ('bachelor', 'master', 'project', 'other')
        title: Thesis title (optional)
        student_ids: List of student IDs associated with the thesis
        theses: List of thesis dictionaries
        title_threshold: Minimum title similarity threshold

    Returns:
        List of tuples (thesis, score, reason) sorted by score
    """
    matches = []

    for thesis in theses:
        reasons = []
        score_components = []

        # Check thesis type match
        if thesis_type and thesis.get('thesis_type'):
            if normalize_string(thesis_type) == normalize_string(thesis['thesis_type']):
                score_components.append(1.0)
                reasons.append("same type")
            else:
                # Different thesis type - very unlikely to be the same thesis
                continue

        # Check student overlap
        thesis_student_ids = [s['id'] if isinstance(s, dict) else s for s in thesis.get('students', [])]
        common_students = set(student_ids) & set(thesis_student_ids)

        if student_ids and thesis_student_ids:
            student_overlap = len(common_students) / max(len(student_ids), len(thesis_student_ids))
            score_components.append(student_overlap)
            if common_students:
                reasons.append(f"{len(common_students)} student(s) match")

        # Check title similarity if both titles exist
        if title and thesis.get('title'):
            title_sim = similarity_ratio(title, thesis['title'])
            if title_sim >= title_threshold:
                score_components.append(title_sim)
                reasons.append(f"title similarity: {title_sim:.0%}")

        # Calculate overall score
        if score_components:
            overall_score = sum(score_components) / len(score_components)
            reason_str = ", ".join(reasons)
            matches.append((thesis, overall_score, reason_str))

    # Sort by score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def format_person_display(person: Dict[str, Any], score: float) -> str:
    """
    Format a person (student or supervisor) for display with their match score.

    Args:
        person: Person dictionary
        score: Match score (0.0 to 1.0)

    Returns:
        Formatted string
    """
    name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    email = person.get('email', 'no email')
    student_id = person.get('student_id', '')

    result = f"  {name} ({email})"
    if student_id:
        result += f" [ID: {student_id}]"
    result += f" - Match: {score:.0%}"

    return result


def format_thesis_display(thesis: Dict[str, Any], score: float, reason: str = "") -> str:
    """
    Format a thesis for display with match score and reason.

    Args:
        thesis: Thesis dictionary
        score: Match score (0.0 to 1.0)
        reason: Reason for the match

    Returns:
        Formatted string
    """
    title = thesis.get('title', 'Untitled')
    thesis_type = thesis.get('thesis_type', 'unknown')
    phase = thesis.get('phase', 'unknown')

    result = f"  [{thesis_type}] {title} (phase: {phase}) - Match: {score:.0%}"
    if reason:
        result += f" ({reason})"

    return result

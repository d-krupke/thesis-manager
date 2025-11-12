"""
Thesis Manager API Client for interacting with the thesis management system.

This module handles all interactions with the Thesis Manager REST API including:
- Fetching theses by phase and status
- Creating automated comments on theses
- Knox token-based authentication
"""

import os
import logging
from typing import List, Dict, Optional, Any
import requests

logger = logging.getLogger(__name__)


class ThesisManagerClient:
    """
    Handles Thesis Manager API interactions for fetching theses and creating comments.

    Uses Knox token authentication.
    """

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Thesis Manager API client.

        Args:
            url: Thesis Manager URL (defaults to THESIS_MANAGER_URL env var)
            token: Knox API token (defaults to THESIS_MANAGER_API_TOKEN env var)
        """
        self.url = (url or os.environ.get("THESIS_MANAGER_URL", "")).rstrip('/')
        self.token = token or os.environ.get("THESIS_MANAGER_API_TOKEN")

        if not self.url:
            raise ValueError("THESIS_MANAGER_URL not set in environment")
        if not self.token:
            raise ValueError("THESIS_MANAGER_API_TOKEN not set in environment")

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
        })
        logger.info("Initialized Thesis Manager client for %s", self.url)

    def get_active_theses(self) -> List[Dict[str, Any]]:
        """
        Fetch all theses in "working" phase with repositories.

        Strategy (two-stage fetch to avoid modifying list serializer):
        1. Fetch list of all theses (ThesisListSerializer - has phase but not git_repository)
        2. Filter for "working" phase only
        3. Fetch full details for each working thesis (ThesisSerializer - has git_repository)
        4. Keep only those with repositories

        This approach is more efficient than fetching full details for all theses,
        and keeps the list serializer optimized for general use.

        Returns:
            List of thesis dictionaries with full details including git_repository
        """
        # Only process theses in working phase
        target_phase = 'working'

        all_theses = []
        url = f"{self.url}/api/theses/"

        try:
            logger.info("Fetching theses list from API...")
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            # Handle paginated response or list response
            if isinstance(data, dict) and 'results' in data:
                theses = data['results']
                logger.debug("API returned paginated response with %d results", len(theses))
            elif isinstance(data, list):
                theses = data
                logger.debug("API returned list with %d theses", len(theses))
            else:
                logger.error("Unexpected API response format: %s", type(data))
                logger.debug("Response keys: %s", list(data.keys()) if isinstance(data, dict) else "not a dict")
                return []

            logger.info("Total theses from API: %d", len(theses))

            # Filter for working phase (from list view)
            working_thesis_ids = []
            other_phases_count = {}

            for thesis in theses:
                if not isinstance(thesis, dict):
                    logger.warning("Skipping non-dict thesis entry: %s", type(thesis))
                    continue

                thesis_id = thesis.get('id')
                phase = thesis.get('phase', '')
                title = thesis.get('title', 'Untitled')[:50]

                logger.debug("Thesis #%d: phase=%s, title=%s", thesis_id, phase, title)

                if phase == target_phase:
                    working_thesis_ids.append(thesis_id)
                    logger.debug("  -> Working phase, will fetch details")
                else:
                    other_phases_count[phase] = other_phases_count.get(phase, 0) + 1
                    logger.debug("  -> EXCLUDED (phase: %s)", phase)

            logger.info("Theses in 'working' phase: %d", len(working_thesis_ids))
            logger.info("Theses in other phases: %d", sum(other_phases_count.values()))
            if logger.isEnabledFor(logging.DEBUG):
                for phase, count in sorted(other_phases_count.items()):
                    logger.debug("  Phase '%s': %d", phase, count)

            # Fetch full details for working theses to get git_repository
            logger.info("Fetching full details for %d working theses...", len(working_thesis_ids))
            theses_with_repos = 0

            for thesis_id in working_thesis_ids:
                thesis_detail = self.get_thesis_by_id(thesis_id, log_fetch=False)
                if thesis_detail:
                    repo = thesis_detail.get('git_repository', '').strip()
                    if repo:
                        theses_with_repos += 1
                        all_theses.append(thesis_detail)
                        logger.debug("Thesis #%d has repository: %s", thesis_id, repo)
                    else:
                        logger.debug("Thesis #%d has no repository", thesis_id)

            logger.info("Working theses with repositories: %d", theses_with_repos)
            logger.info("Working theses without repositories: %d",
                       len(working_thesis_ids) - theses_with_repos)

            return all_theses

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching theses: %s", e)
            return []

    def get_thesis_by_id(self, thesis_id: int, log_fetch: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific thesis by ID.

        Args:
            thesis_id: Thesis ID
            log_fetch: Whether to log the fetch operation (set False for batch operations)

        Returns:
            Thesis dictionary or None if not found
        """
        url = f"{self.url}/api/theses/{thesis_id}/"

        try:
            if log_fetch:
                logger.info("Fetching thesis #%d", thesis_id)
            response = self.session.get(url)
            response.raise_for_status()
            thesis = response.json()
            if log_fetch:
                logger.debug("Retrieved thesis: %s", thesis.get('title', 'Untitled'))
            return thesis

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching thesis %d: %s", thesis_id, e)
            return None

    def create_comment(
        self,
        thesis_id: int,
        text: str,
        is_auto_generated: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Create a comment on a thesis.

        Args:
            thesis_id: Thesis ID
            text: Comment text
            is_auto_generated: Whether this is an auto-generated comment

        Returns:
            Created comment dictionary or None if failed
        """
        url = f"{self.url}/api/theses/{thesis_id}/add_comment/"

        payload = {
            'text': text,
            'is_auto_generated': is_auto_generated,
        }

        try:
            logger.info("Creating comment on thesis #%d (%d characters)",
                       thesis_id, len(text))
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            comment = response.json()
            logger.info("Comment created successfully (ID: %s)", comment.get('id'))
            return comment

        except requests.exceptions.RequestException as e:
            logger.error("Error creating comment on thesis %d: %s", thesis_id, e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %d", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
                try:
                    error_detail = e.response.json()
                    logger.error("Error details: %s", error_detail)
                except:
                    pass
            return None

    # Student operations
    def list_students(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all students, optionally filtered by search term.

        Args:
            search: Optional search term for name, email, or student_id

        Returns:
            List of student dictionaries
        """
        url = f"{self.url}/api/students/"
        params = {}
        if search:
            params['search'] = search

        try:
            logger.info("Fetching students list (search: %s)", search or "none")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Handle paginated or list response
            if isinstance(data, dict) and 'results' in data:
                students = data['results']
            elif isinstance(data, list):
                students = data
            else:
                logger.error("Unexpected response format from students API")
                return []

            logger.info("Retrieved %d students", len(students))
            return students

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching students: %s", e)
            return []

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific student by ID.

        Args:
            student_id: Student ID

        Returns:
            Student dictionary or None if not found
        """
        url = f"{self.url}/api/students/{student_id}/"

        try:
            logger.info("Fetching student #%d", student_id)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching student %d: %s", student_id, e)
            return None

    def create_student(
        self,
        first_name: str,
        last_name: str,
        email: str,
        student_id: Optional[str] = None,
        comments: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new student.

        Args:
            first_name: Student's first name
            last_name: Student's last name
            email: Student's email address (must be unique)
            student_id: Optional student/matriculation number
            comments: Optional free-text comments

        Returns:
            Created student dictionary or None if failed
        """
        url = f"{self.url}/api/students/"

        payload = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }
        if student_id:
            payload['student_id'] = student_id
        if comments:
            payload['comments'] = comments

        try:
            logger.info("Creating student: %s %s (%s)", first_name, last_name, email)
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            student = response.json()
            logger.info("Student created successfully (ID: %s)", student.get('id'))
            return student

        except requests.exceptions.RequestException as e:
            logger.error("Error creating student: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %d", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
            return None

    # Supervisor operations
    def list_supervisors(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all supervisors, optionally filtered by search term.

        Args:
            search: Optional search term for name or email

        Returns:
            List of supervisor dictionaries
        """
        url = f"{self.url}/api/supervisors/"
        params = {}
        if search:
            params['search'] = search

        try:
            logger.info("Fetching supervisors list (search: %s)", search or "none")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Handle paginated or list response
            if isinstance(data, dict) and 'results' in data:
                supervisors = data['results']
            elif isinstance(data, list):
                supervisors = data
            else:
                logger.error("Unexpected response format from supervisors API")
                return []

            logger.info("Retrieved %d supervisors", len(supervisors))
            return supervisors

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching supervisors: %s", e)
            return []

    def get_supervisor_by_id(self, supervisor_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific supervisor by ID.

        Args:
            supervisor_id: Supervisor ID

        Returns:
            Supervisor dictionary or None if not found
        """
        url = f"{self.url}/api/supervisors/{supervisor_id}/"

        try:
            logger.info("Fetching supervisor #%d", supervisor_id)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching supervisor %d: %s", supervisor_id, e)
            return None

    def create_supervisor(
        self,
        first_name: str,
        last_name: str,
        email: str,
        comments: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new supervisor.

        Args:
            first_name: Supervisor's first name
            last_name: Supervisor's last name
            email: Supervisor's email address (must be unique)
            comments: Optional free-text comments

        Returns:
            Created supervisor dictionary or None if failed
        """
        url = f"{self.url}/api/supervisors/"

        payload = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }
        if comments:
            payload['comments'] = comments

        try:
            logger.info("Creating supervisor: %s %s (%s)", first_name, last_name, email)
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            supervisor = response.json()
            logger.info("Supervisor created successfully (ID: %s)", supervisor.get('id'))
            return supervisor

        except requests.exceptions.RequestException as e:
            logger.error("Error creating supervisor: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %d", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
            return None

    # Thesis operations
    def list_theses(
        self,
        phase: Optional[str] = None,
        thesis_type: Optional[str] = None,
        student: Optional[int] = None,
        supervisor: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all theses with optional filtering.

        Args:
            phase: Filter by phase (e.g., 'working', 'completed', 'abandoned')
            thesis_type: Filter by type (e.g., 'bachelor', 'master', 'project')
            student: Filter by student ID
            supervisor: Filter by supervisor ID
            search: Search in title, description, and student names

        Returns:
            List of thesis dictionaries
        """
        url = f"{self.url}/api/theses/"
        params = {}
        if phase:
            params['phase'] = phase
        if thesis_type:
            params['thesis_type'] = thesis_type
        if student:
            params['students'] = student
        if supervisor:
            params['supervisors'] = supervisor
        if search:
            params['search'] = search

        try:
            logger.info("Fetching theses list with filters: %s", params)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Handle paginated or list response
            if isinstance(data, dict) and 'results' in data:
                theses = data['results']
            elif isinstance(data, list):
                theses = data
            else:
                logger.error("Unexpected response format from theses API")
                return []

            logger.info("Retrieved %d theses", len(theses))
            return theses

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching theses: %s", e)
            return []

    def create_thesis(
        self,
        thesis_type: str,
        student_ids: List[int],
        supervisor_ids: List[int],
        title: Optional[str] = None,
        phase: str = 'first_contact',
        date_first_contact: Optional[str] = None,
        date_topic_selected: Optional[str] = None,
        date_registration: Optional[str] = None,
        date_deadline: Optional[str] = None,
        date_presentation: Optional[str] = None,
        date_review: Optional[str] = None,
        date_final_discussion: Optional[str] = None,
        description: Optional[str] = None,
        task_description: Optional[str] = None,
        git_repository: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new thesis.

        Args:
            thesis_type: Type of thesis ('bachelor', 'master', 'project', 'other')
            student_ids: List of student IDs
            supervisor_ids: List of supervisor IDs
            title: Thesis title (optional, can be added later)
            phase: Current phase (default: 'first_contact')
            date_first_contact: First contact date (YYYY-MM-DD format)
            date_topic_selected: Topic selection date
            date_registration: Registration date
            date_deadline: Submission deadline
            date_presentation: Presentation/defense date
            date_review: Review completion date
            date_final_discussion: Final discussion date
            description: General description
            task_description: Formal task description
            git_repository: URL to student's git repository

        Returns:
            Created thesis dictionary or None if failed
        """
        url = f"{self.url}/api/theses/"

        payload = {
            'thesis_type': thesis_type,
            'students': student_ids,
            'supervisors': supervisor_ids,
            'phase': phase,
        }

        # Add optional fields
        if title:
            payload['title'] = title
        if date_first_contact:
            payload['date_first_contact'] = date_first_contact
        if date_topic_selected:
            payload['date_topic_selected'] = date_topic_selected
        if date_registration:
            payload['date_registration'] = date_registration
        if date_deadline:
            payload['date_deadline'] = date_deadline
        if date_presentation:
            payload['date_presentation'] = date_presentation
        if date_review:
            payload['date_review'] = date_review
        if date_final_discussion:
            payload['date_final_discussion'] = date_final_discussion
        if description:
            payload['description'] = description
        if task_description:
            payload['task_description'] = task_description
        if git_repository:
            payload['git_repository'] = git_repository

        try:
            logger.info("Creating thesis: %s (type: %s)", title or "Untitled", thesis_type)
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            thesis = response.json()
            logger.info("Thesis created successfully (ID: %s)", thesis.get('id'))
            return thesis

        except requests.exceptions.RequestException as e:
            logger.error("Error creating thesis: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response status: %d", e.response.status_code)
                logger.error("Response body: %s", e.response.text)
            return None

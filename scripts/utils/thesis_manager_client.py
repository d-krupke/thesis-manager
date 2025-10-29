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

"""
GitLab API Client for fetching repository activity.

This module handles all interactions with the GitLab API including:
- Project discovery and access
- Commit history retrieval
- Diff analysis and file change tracking
"""

import os
import sys
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import gitlab

logger = logging.getLogger(__name__)


class GitLabClient:
    """
    Handles GitLab API interactions for fetching repository activity.

    This class encapsulates all GitLab operations, making it easy to
    extend or mock for testing.
    """

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize GitLab client.

        Args:
            url: GitLab instance URL (defaults to GITLAB_URL env var)
            token: GitLab access token (defaults to GITLAB_TOKEN env var)
        """
        self.url = url or os.environ.get("GITLAB_URL", "https://gitlab.com")
        self.token = token or os.environ.get("GITLAB_TOKEN")

        if not self.token:
            raise ValueError("GITLAB_TOKEN not set in environment")

        self.gl = gitlab.Gitlab(self.url, private_token=self.token)
        logger.info("Initialized GitLab client for %s", self.url)

    def get_project_by_path(self, project_path: str):
        """
        Get a GitLab project by its path.

        Args:
            project_path: Project path (e.g., 'group/subgroup/project')

        Returns:
            GitLab project object or None if not found/accessible
        """
        try:
            logger.debug("Fetching GitLab project: %s", project_path)
            return self.gl.projects.get(project_path)
        except gitlab.exceptions.GitlabGetError as e:
            logger.warning("Could not access project '%s': %s", project_path, e)
            return None

    def extract_project_path_from_url(self, repo_url: str) -> Optional[str]:
        """
        Extract GitLab project path from repository URL.

        Examples:
            'https://gitlab.com/group/project' -> 'group/project'
            'https://gitlab.com/group/project.git' -> 'group/project'
            'git@gitlab.com:group/project.git' -> 'group/project'

        Args:
            repo_url: Git repository URL

        Returns:
            Project path or None if URL is invalid
        """
        if not repo_url:
            return None

        # Handle SSH URLs (git@host:path.git)
        if repo_url.startswith('git@'):
            match = re.match(r'git@[^:]+:(.+?)(?:\.git)?$', repo_url)
            if match:
                return match.group(1)

        # Handle HTTPS URLs
        parsed = urlparse(repo_url)
        if parsed.path:
            # Remove leading slash and trailing .git
            path = parsed.path.lstrip('/')
            if path.endswith('.git'):
                path = path[:-4]
            return path

        return None

    def collect_recent_commits(
        self,
        project,
        since_utc: datetime,
        until_utc: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect commits from all branches within a time range.

        Args:
            project: GitLab project object
            since_utc: Start of time range (inclusive)
            until_utc: End of time range (exclusive)

        Returns:
            List of commit dictionaries with metadata
        """
        branches = project.branches.list(all=True)
        logger.info("Scanning %d branches for commits between %s and %s",
                   len(branches), since_utc.date(), until_utc.date())
        seen = {}  # sha -> commit summary dict

        for br in branches:
            br_name = br.name
            try:
                page_commits = project.commits.list(
                    ref_name=br_name,
                    since=self._iso_utc(since_utc),
                    until=self._iso_utc(until_utc),
                    all=True,
                    per_page=100,
                )
            except Exception as e:
                logger.warning("Could not fetch commits from branch '%s': %s", br_name, e)
                continue

            for c in page_commits:
                sha = c.id
                if sha not in seen:
                    try:
                        # Fetch details to get stats + diff
                        details = project.commits.get(sha)
                        stats = getattr(details, "stats", {}) or {}
                        additions = stats.get("additions", 0)
                        deletions = stats.get("deletions", 0)

                        # Get file changes
                        diffs = details.diff()
                        files_changed = self._parse_diff_files(diffs)

                        # Normalize timestamp
                        created_at = datetime.fromisoformat(c.created_at.replace('Z', '+00:00'))

                        seen[sha] = {
                            "sha": sha,
                            "short": sha[:8],
                            "title": c.title,
                            "author": c.author_name,
                            "email": c.author_email,
                            "date": created_at,
                            "additions": additions,
                            "deletions": deletions,
                            "files": files_changed,
                            "branches": {br_name},
                        }
                    except Exception as e:
                        logger.warning("Could not fetch details for commit %s: %s", sha[:8], e)
                        continue
                else:
                    seen[sha]["branches"].add(br_name)

        # Sort newest → oldest by commit date
        commits = sorted(seen.values(), key=lambda x: x["date"], reverse=True)
        logger.info("Found %d unique commits", len(commits))
        return commits

    def _iso_utc(self, dt: datetime) -> str:
        """Convert datetime to ISO 8601 format for GitLab API."""
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _parse_diff_files(self, diffs: List[Dict]) -> List[str]:
        """Parse diff data to extract file change descriptions."""
        files_changed = []
        for d in diffs:
            new_path = d.get("new_path") or ""
            old_path = d.get("old_path") or ""
            flags = []

            if d.get("new_file"):
                flags.append("new")
            if d.get("renamed_file"):
                flags.append(f"renamed from {old_path}")
            if d.get("deleted_file"):
                flags.append("deleted")

            if flags:
                label = f"{new_path} ({', '.join(flags)})"
            else:
                label = new_path or old_path

            files_changed.append(label)

        return files_changed

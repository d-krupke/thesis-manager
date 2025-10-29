"""
Report Generator for creating activity reports from commit data.

This module provides the base ReportGenerator class which can be extended
to create AI-enhanced report generators in the future.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Base class for generating reports from commit data.

    This class can be extended to create AI-enhanced report generators
    in the future (e.g., AIReportGenerator that uses LLMs to analyze
    commits and generate insights).

    For now, it generates simple markdown-formatted reports.
    """

    def generate_report(
        self,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> str:
        """
        Generate a report from commit data.

        Args:
            commits: List of commit dictionaries
            thesis: Thesis dictionary
            days: Number of days analyzed

        Returns:
            Formatted report text (markdown)
        """
        if not commits:
            return self._generate_no_activity_report(thesis, days)

        return self._generate_activity_report(commits, thesis, days)

    def _generate_no_activity_report(self, thesis: Dict[str, Any], days: int) -> str:
        """Generate report when there are no commits."""
        title = thesis.get('title', 'Untitled')
        return (
            f"## Weekly Repository Activity Report\n\n"
            f"**Thesis**: {title}\n"
            f"**Period**: Last {days} days\n"
            f"**Status**: No commits found\n\n"
            f"ℹ️ No activity detected in the repository during this period.\n"
        )

    def _generate_activity_report(
        self,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> str:
        """Generate report with commit activity."""
        title = thesis.get('title', 'Untitled')

        # Calculate statistics
        total_additions = sum(c['additions'] for c in commits)
        total_deletions = sum(c['deletions'] for c in commits)
        unique_authors = set(c['author'] for c in commits)

        # Build report
        lines = [
            f"## Weekly Repository Activity Report\n",
            f"**Thesis**: {title}",
            f"**Period**: Last {days} days",
            f"**Commits**: {len(commits)}",
            f"**Authors**: {', '.join(sorted(unique_authors))}",
            f"**Changes**: +{total_additions} / -{total_deletions} lines\n",
            f"### Commits\n",
        ]

        # Add individual commits
        for commit in commits:
            date_str = commit['date'].strftime("%Y-%m-%d %H:%M")
            branches = ', '.join(sorted(commit['branches']))

            lines.append(
                f"**{commit['short']}** - {commit['title']}  \n"
                f"*{commit['author']}* | {date_str} | "
                f"+{commit['additions']}/-{commit['deletions']} lines | "
                f"branches: {branches}"
            )

            if commit['files']:
                lines.append("\nFiles changed:")
                for file_path in commit['files'][:10]:  # Limit to 10 files
                    lines.append(f"  - `{file_path}`")
                if len(commit['files']) > 10:
                    lines.append(f"  - *(and {len(commit['files']) - 10} more files)*")

            lines.append("")  # Blank line between commits

        return "\n".join(lines)

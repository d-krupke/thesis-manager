#!/usr/bin/env python3
"""
GitLab Weekly Reporter for Thesis Manager

This script automatically generates weekly activity reports for student theses
by analyzing their GitLab repositories and posting comments to the thesis manager.

Architecture (designed for AI extension):
  1. GitLabClient - Handles GitLab API interactions (utils/gitlab_client.py)
  2. ThesisManagerClient - Handles Thesis Manager API interactions (utils/thesis_manager_client.py)
  3. ReportGenerator - Generates reports (utils/report_generator.py - base class for future AI enhancement)
  4. Main orchestrator - Coordinates the workflow (this file)

Environment variables (from .env):
  GITLAB_URL                 - GitLab instance URL
  GITLAB_TOKEN              - GitLab personal access token
  THESIS_MANAGER_URL        - Thesis Manager instance URL
  THESIS_MANAGER_API_TOKEN  - Knox authentication token

Usage examples:
  # Generate reports for all active theses
  python gitlab_reporter.py

  # Test with a specific thesis ID
  python gitlab_reporter.py --thesis-id 5

  # Test mode (dry-run, no comments created)
  python gitlab_reporter.py --dry-run

  # Custom lookback period
  python gitlab_reporter.py --days 14
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import dotenv

# Import utility modules
from utils import GitLabClient, ThesisManagerClient, ReportGenerator

dotenv.load_dotenv(dotenv.find_dotenv())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Main Orchestration - Process theses and generate reports
# ============================================================================

def process_thesis(
    thesis: Dict[str, Any],
    gitlab_client: GitLabClient,
    tm_client: ThesisManagerClient,
    report_gen: ReportGenerator,
    days: int,
    dry_run: bool
) -> bool:
    """
    Process a single thesis: fetch commits and create report.

    Args:
        thesis: Thesis dictionary
        gitlab_client: GitLab client instance
        tm_client: Thesis Manager client instance
        report_gen: Report generator instance
        days: Number of days to look back
        dry_run: If True, don't actually create comments

    Returns:
        True if successful, False otherwise
    """
    thesis_id = thesis['id']
    title = thesis.get('title', 'Untitled')
    repo_url = thesis.get('git_repository', '')

    logger.info("="*70)
    logger.info("Processing thesis #%d: %s", thesis_id, title)
    logger.info("Repository: %s", repo_url)

    # Extract project path from URL
    project_path = gitlab_client.extract_project_path_from_url(repo_url)
    if not project_path:
        logger.warning("Could not extract project path from URL: %s", repo_url)
        return False

    logger.info("GitLab project: %s", project_path)

    # Get GitLab project
    project = gitlab_client.get_project_by_path(project_path)
    if not project:
        logger.warning("Could not access GitLab project (check permissions)")
        return False

    # Fetch commits
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    logger.info("Fetching commits from %s to %s", since.date(), now.date())
    commits = gitlab_client.collect_recent_commits(project, since, now)

    # Generate report
    report = report_gen.generate_report(commits, thesis, days)

    if dry_run:
        logger.info("[DRY RUN] Would create comment with %d characters", len(report))
        logger.debug("Report preview:\n%s", report)
        return True

    # Create comment
    comment = tm_client.create_comment(thesis_id, report, is_auto_generated=True)

    if comment:
        return True
    else:
        logger.error("Failed to create comment")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate weekly repository activity reports for theses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all active theses
  python gitlab_reporter.py

  # Test with specific thesis
  python gitlab_reporter.py --thesis-id 5

  # Dry run (don't create comments)
  python gitlab_reporter.py --dry-run

  # Custom time period
  python gitlab_reporter.py --days 14

  # Verbose output
  python gitlab_reporter.py --verbose
        """
    )

    parser.add_argument(
        '--thesis-id',
        type=int,
        help='Process only this specific thesis ID'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Look-back window in days (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without creating comments'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    # Adjust logging level if verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("GitLab Weekly Reporter starting...")
    logger.info("Configuration: lookback=%d days, dry_run=%s", args.days, args.dry_run)

    # Initialize clients
    try:
        gitlab_client = GitLabClient()
        tm_client = ThesisManagerClient()
        report_gen = ReportGenerator()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        logger.error("Please ensure the following environment variables are set:")
        logger.error("  - GITLAB_URL")
        logger.error("  - GITLAB_TOKEN")
        logger.error("  - THESIS_MANAGER_URL")
        logger.error("  - THESIS_MANAGER_API_TOKEN")
        sys.exit(1)

    # Fetch theses
    if args.thesis_id:
        thesis = tm_client.get_thesis_by_id(args.thesis_id)
        if not thesis:
            logger.error("Thesis #%d not found", args.thesis_id)
            sys.exit(1)
        theses = [thesis]
    else:
        theses = tm_client.get_active_theses()

    if not theses:
        logger.info("No theses to process")
        sys.exit(0)

    logger.info("Found %d thesis/theses to process", len(theses))

    # Process each thesis
    success_count = 0
    failure_count = 0

    for thesis in theses:
        try:
            if process_thesis(thesis, gitlab_client, tm_client, report_gen, args.days, args.dry_run):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.exception("Unexpected error processing thesis #%d: %s",
                           thesis.get('id', 'unknown'), e)
            failure_count += 1

    # Summary
    logger.info("="*70)
    logger.info("Summary:")
    logger.info("  Processed: %d thesis/theses", len(theses))
    logger.info("  Success: %d", success_count)
    logger.info("  Failed: %d", failure_count)

    if args.dry_run:
        logger.info("(Dry run mode - no comments were actually created)")


if __name__ == "__main__":
    main()

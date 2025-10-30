#!/usr/bin/env -S uv run --quiet
# /// script
# dependencies = [
#   "python-gitlab>=4.0.0",
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
#   "pydantic-ai>=0.0.14",
#   "pydantic>=2.0.0",
#   "openai>=1.52.0",
# ]
# ///
"""
GitLab Weekly Reporter for Thesis Manager

This script automatically generates weekly activity reports for student theses
by analyzing their GitLab repositories and posting comments to the thesis manager.

Features:
  - Basic commit activity reports with statistics and file changes
  - AI-powered progress analysis with ChatGPT (optional, with --ai flag)
  - Automatic error reporting: posts comments when repository access fails
  - Email notifications to supervisors (via thesis manager)
  - Comprehensive audit logging for AI interactions

Architecture (designed for AI extension):
  1. GitLabClient - Handles GitLab API interactions (utils/gitlab_client.py)
  2. ThesisManagerClient - Handles Thesis Manager API interactions (utils/thesis_manager_client.py)
  3. ReportGenerator - Generates reports (utils/report_generator.py - base class for future AI enhancement)
  4. Main orchestrator - Coordinates the workflow (this file)

Error Handling:
  When repository analysis fails (invalid URL, access denied, API errors), the script
  automatically posts an error comment to the thesis with:
  - Clear error description
  - Possible causes
  - Action items for resolution
  These error comments trigger email notifications to supervisors.

Environment variables (from .env):
  GITLAB_URL                 - GitLab instance URL
  GITLAB_TOKEN              - GitLab personal access token
  THESIS_MANAGER_URL        - Thesis Manager instance URL
  THESIS_MANAGER_API_TOKEN  - Knox authentication token
  OPENAI_API_KEY            - OpenAI API key (for AI analysis)

Usage with uv (recommended - auto-manages dependencies):
  ./gitlab_reporter.py --ai              # With AI analysis
  ./gitlab_reporter.py --thesis-id 5     # Test specific thesis
  ./gitlab_reporter.py --dry-run --ai    # Test mode (no comments posted)
  ./gitlab_reporter.py --days 14         # Custom period

Usage with python (requires manual dependency installation):
  python gitlab_reporter.py --ai
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import dotenv

# Import utility modules
from utils import GitLabClient, ThesisManagerClient, ReportGenerator, AIReportGenerator

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
        error_msg = (
            "⚠️ **Automatic Weekly Report - Error**\n\n"
            f"Could not analyze repository activity for the past {days} days.\n\n"
            "**Error:** Invalid GitLab repository URL.\n\n"
            "**Details:** The repository URL could not be parsed. Please verify that the "
            "GitLab repository URL is correct and follows the expected format "
            "(e.g., `https://gitlab.example.com/group/project`).\n\n"
            f"**Repository URL:** `{repo_url}`\n\n"
            "**Action Required:** Please update the repository URL in the thesis settings."
        )
        logger.warning("Could not extract project path from URL: %s", repo_url)

        if not dry_run:
            tm_client.create_comment(thesis_id, error_msg, is_auto_generated=True)
        else:
            logger.info("[DRY RUN] Would create error comment")

        return False

    logger.info("GitLab project: %s", project_path)

    # Get GitLab project
    project = gitlab_client.get_project_by_path(project_path)
    if not project:
        error_msg = (
            "⚠️ **Automatic Weekly Report - Error**\n\n"
            f"Could not analyze repository activity for the past {days} days.\n\n"
            "**Error:** GitLab repository not accessible.\n\n"
            "**Possible causes:**\n"
            "- The repository does not exist or has been moved/renamed\n"
            "- The bot account does not have access permissions to this repository\n"
            "- The repository is private and access has not been granted\n"
            "- The GitLab server is temporarily unavailable\n\n"
            f"**Repository URL:** `{repo_url}`\n"
            f"**Project Path:** `{project_path}`\n\n"
            "**Action Required:** Please verify the repository exists and grant read access "
            "to the thesis manager bot account."
        )
        logger.warning("Could not access GitLab project (check permissions)")

        if not dry_run:
            tm_client.create_comment(thesis_id, error_msg, is_auto_generated=True)
        else:
            logger.info("[DRY RUN] Would create error comment")

        return False

    # Fetch commits
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    logger.info("Fetching commits from %s to %s", since.date(), now.date())

    try:
        commits = gitlab_client.collect_recent_commits(project, since, now)
    except Exception as e:
        error_msg = (
            "⚠️ **Automatic Weekly Report - Error**\n\n"
            f"Could not analyze repository activity for the past {days} days.\n\n"
            "**Error:** Failed to fetch commits from GitLab.\n\n"
            f"**Technical details:** {str(e)}\n\n"
            f"**Repository URL:** `{repo_url}`\n\n"
            "**Action Required:** This might be a temporary issue with the GitLab API. "
            "If the problem persists, please contact the thesis manager administrator."
        )
        logger.error("Failed to fetch commits: %s", e)

        if not dry_run:
            tm_client.create_comment(thesis_id, error_msg, is_auto_generated=True)
        else:
            logger.info("[DRY RUN] Would create error comment")

        return False

    # Generate report
    try:
        report = report_gen.generate_report(commits, thesis, days)
    except Exception as e:
        error_msg = (
            "⚠️ **Automatic Weekly Report - Error**\n\n"
            f"Could not generate progress report for the past {days} days.\n\n"
            "**Error:** Report generation failed.\n\n"
            f"**Technical details:** {str(e)}\n\n"
            "**Action Required:** This is likely a system issue. Please contact the "
            "thesis manager administrator if this problem persists."
        )
        logger.error("Failed to generate report: %s", e)

        if not dry_run:
            tm_client.create_comment(thesis_id, error_msg, is_auto_generated=True)
        else:
            logger.info("[DRY RUN] Would create error comment")

        return False

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

  # Enable AI-powered analysis
  python gitlab_reporter.py --ai

  # AI with specific model
  python gitlab_reporter.py --ai --ai-model gpt-5-mini

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
    parser.add_argument(
        '--ai',
        action='store_true',
        help='Enable AI-powered progress analysis (requires OPENAI_API_KEY)'
    )
    parser.add_argument(
        '--ai-model',
        default='gpt-5-mini',
        help='OpenAI model to use for AI analysis (default: gpt-5-mini)'
    )

    args = parser.parse_args()

    # Adjust logging level if verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("GitLab Weekly Reporter starting...")
    logger.info("Configuration: lookback=%d days, dry_run=%s, ai=%s",
               args.days, args.dry_run, args.ai)

    # Initialize clients
    try:
        gitlab_client = GitLabClient()
        tm_client = ThesisManagerClient()

        # Choose report generator based on --ai flag
        if args.ai:
            logger.info("AI-enhanced reporting enabled with model: %s", args.ai_model)
            report_gen = AIReportGenerator(model=args.ai_model)
        else:
            logger.info("Using basic report generator")
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

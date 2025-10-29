"""
AI-Enhanced Report Generator using ChatGPT to analyze thesis progress.

This module extends the base ReportGenerator to add intelligent analysis
of commit activity and thesis progress using Large Language Models.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ProgressAnalysis(BaseModel):
    """
    Structured analysis of thesis progress.

    This model defines the structured output from the AI analysis,
    ensuring consistent and parseable results.
    """

    summary: str = Field(
        description="Concise summary of where and how much progress was made."
    )

    code_progress_score: int = Field(
        ge=0, le=10,
        description="Score from 0-10 indicating implementation progress. "
                   "0 = no progress, 10 = excellent progress"
    )

    thesis_progress_score: int = Field(
        ge=0, le=10,
        description="Score from 0-10 indicating thesis writing progress (LaTeX). "
                   "0 = no progress, 10 = excellent progress"
    )

    needs_attention: bool = Field(
        description="True if progress appears too slow and supervisor should be alerted"
    )

    reasoning: str = Field(
        description="Brief explanation of the scores and attention flag (1-2 sentences)"
    )


class AIReportGenerator(ReportGenerator):
    """
    AI-enhanced report generator using ChatGPT for intelligent analysis.

    Extends the base ReportGenerator to add AI-powered progress analysis
    at the top of reports. Falls back to basic reporting if AI is unavailable.
    """

    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize AI report generator.

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
        """
        super().__init__()

        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model_name = model

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - AI analysis will be disabled")
            self.agent = None
        else:
            # Set API key in environment for pydantic-ai
            os.environ['OPENAI_API_KEY'] = self.api_key

            # Initialize pydantic-ai agent with OpenAI model
            try:
                # pydantic-ai uses environment variable for API key
                # Model string format: 'openai:model-name'
                self.agent = Agent(
                    f'openai:{self.model_name}',
                    output_type=ProgressAnalysis,
                    system_prompt=self._build_system_prompt()
                )
                logger.info("Initialized AI report generator with model: %s", self.model_name)
            except Exception as e:
                logger.error("Failed to initialize AI agent: %s", e)
                self.agent = None

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI agent."""
        return """You are an expert thesis supervisor analyzing student progress.

Your task is to analyze Git commit activity and provide a structured assessment for the professor.

Consider:
- Commit frequency and consistency
- Code changes (additions/deletions)
- Areas of progress
- File types modified (implementation vs thesis writing)
- Commit messages quality
- Time remaining until deadline
- Expected progress based on registration date

Be realistic but encouraging. Flag issues early to help students succeed.

For code_progress_score (0-10):
- 0-2: No meaningful code changes
- 3-4: Minimal progress, concerning
- 5-6: Some progress, but could be better
- 7-8: Good, steady progress
- 9-10: Excellent, substantial progress

For thesis_progress_score (0-10):
- Look for LaTeX files (.tex)
- 0-2: No thesis writing detected
- 3-4: Minimal writing
- 5-6: Some writing progress
- 7-8: Good writing progress
- 9-10: Substantial thesis writing

Set needs_attention=true if:
- Very low activity with deadline approaching
- No progress for extended period
- Concerning patterns (e.g., only last-minute work)
"""

    def generate_report(
        self,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> str:
        """
        Generate AI-enhanced report with progress analysis.

        Args:
            commits: List of commit dictionaries
            thesis: Thesis dictionary
            days: Number of days analyzed

        Returns:
            Formatted markdown report with AI analysis at the top
        """
        # Generate base report
        base_report = super().generate_report(commits, thesis, days)

        # Check if AI analysis is enabled for this thesis
        ai_enabled = thesis.get('ai_summary_enabled', True)  # Default to True for backwards compatibility

        if not ai_enabled:
            logger.info("AI analysis disabled for thesis #%d (student consent not given)", thesis.get('id'))
            return base_report

        # Add AI analysis if available and there are commits
        if self.agent and commits:
            try:
                analysis = self._analyze_progress(commits, thesis, days)
                enhanced_report = self._format_enhanced_report(
                    analysis, base_report, commits, thesis, days
                )
                return enhanced_report
            except Exception as e:
                logger.error("AI analysis failed, falling back to basic report: %s", e)
                return base_report

        return base_report

    def _analyze_progress(
        self,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> ProgressAnalysis:
        """
        Use AI to analyze progress from commit data.

        Args:
            commits: List of commit dictionaries
            thesis: Thesis dictionary
            days: Number of days analyzed

        Returns:
            Structured progress analysis
        """
        # Build context for AI
        context = self._build_analysis_context(commits, thesis, days)

        # Run AI analysis
        logger.debug("Running AI analysis for thesis #%d", thesis.get('id'))
        result = self.agent.run_sync(context)

        logger.debug("AI analysis complete: score=%d/%d, attention=%s",
                    result.output.code_progress_score,
                    result.output.thesis_progress_score,
                    result.output.needs_attention)

        return result.output

    def _build_analysis_context(
        self,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> str:
        """
        Build context string for AI analysis.

        Args:
            commits: List of commit dictionaries
            thesis: Thesis dictionary
            days: Number of days analyzed

        Returns:
            Context string describing the situation
        """
        title = thesis.get('title', 'Untitled')
        date_registration = thesis.get('date_registration')
        date_deadline = thesis.get('date_deadline')

        # Calculate time information
        now = datetime.now(timezone.utc)
        time_info = []

        if date_registration:
            try:
                reg_date = datetime.fromisoformat(str(date_registration))
                if reg_date.tzinfo is None:
                    reg_date = reg_date.replace(tzinfo=timezone.utc)
                days_since_reg = (now - reg_date).days
                time_info.append(f"Days since registration: {days_since_reg}")
            except:
                pass

        if date_deadline:
            try:
                deadline = datetime.fromisoformat(str(date_deadline))
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                days_until_deadline = (deadline - now).days
                time_info.append(f"Days until deadline: {days_until_deadline}")
            except:
                pass

        # Analyze file types
        code_files = []
        thesis_files = []
        other_files = []

        for commit in commits:
            for file_path in commit['files']:
                file_lower = file_path.lower()
                if any(ext in file_lower for ext in ['.py', '.java', '.cpp', '.c', '.js', '.ts', '.rs', '.go', '.h', '.hpp']):
                    code_files.append(file_path)
                elif any(ext in file_lower for ext in ['.tex', '.bib', '.md', 'readme']):
                    thesis_files.append(file_path)
                else:
                    other_files.append(file_path)

        # Calculate statistics
        total_additions = sum(c['additions'] for c in commits)
        total_deletions = sum(c['deletions'] for c in commits)

        # Build context
        lines = [
            f"Thesis: {title}",
            f"Analysis period: Last {days} days",
            "",
        ]

        if time_info:
            lines.extend(time_info)
            lines.append("")

        # Add custom context if provided
        ai_context = thesis.get('ai_context', '').strip()
        if ai_context:
            lines.append("Important context:")
            lines.append(f"  {ai_context}")
            lines.append("")

        lines.extend([
            f"Commits: {len(commits)}",
            f"Total changes: +{total_additions}/-{total_deletions} lines",
            "",
            f"File analysis:",
            f"  - Code files modified: {len(set(code_files))}",
            f"  - Thesis/doc files modified: {len(set(thesis_files))}",
            f"  - Other files: {len(set(other_files))}",
            "",
            "Recent commits (newest first):",
        ])

        # Add commit details (limit to prevent token overflow)
        for i, commit in enumerate(commits[:10]):  # Limit to 10 most recent
            # Handle both datetime objects and strings
            commit_date = commit['date']
            if isinstance(commit_date, datetime):
                date_str = commit_date.strftime("%Y-%m-%d")
            elif isinstance(commit_date, str):
                # Extract date portion from string (format: "YYYY-MM-DD HH:MM:SS")
                date_str = commit_date.split()[0] if ' ' in commit_date else commit_date
            else:
                date_str = str(commit_date)

            lines.append(
                f"  {i+1}. [{date_str}] {commit['title']} "
                f"(+{commit['additions']}/-{commit['deletions']})"
            )

            # Add file paths (limit to 10 files per commit)
            files = commit.get('files', [])
            if files:
                files_to_show = files[:10]
                for file_path in files_to_show:
                    lines.append(f"      - {file_path}")
                if len(files) > 10:
                    lines.append(f"      ... and {len(files) - 10} more files")

        if len(commits) > 10:
            lines.append(f"  ... and {len(commits) - 10} more commits")

        return "\n".join(lines)

    def _format_enhanced_report(
        self,
        analysis: ProgressAnalysis,
        base_report: str,
        commits: List[Dict[str, Any]],
        thesis: Dict[str, Any],
        days: int
    ) -> str:
        """
        Format the enhanced report with AI analysis at the top.

        Args:
            analysis: AI-generated analysis
            base_report: Base report from parent class
            commits: List of commit dictionaries
            thesis: Thesis dictionary
            days: Number of days analyzed

        Returns:
            Enhanced markdown report
        """
        lines = [
            "## Weekly Repository Activity Report\n",
            "### 🤖 AI Progress Analysis\n",
        ]

        # Add attention warning if needed
        if analysis.needs_attention:
            lines.append("⚠️ **Attention Required**\n")

        # Add summary
        lines.extend([
            f"{analysis.summary}\n",
            "**Progress Scores:**",
            f"- Implementation: **{analysis.code_progress_score}/10** ",
            self._get_progress_emoji(analysis.code_progress_score),
            f"- Thesis Writing: **{analysis.thesis_progress_score}/10** ",
            self._get_progress_emoji(analysis.thesis_progress_score),
            "",
            f"*{analysis.reasoning}*\n",
            "---\n",
        ])

        # Extract title and stats from base report and rebuild without redundant header
        title = thesis.get('title', 'Untitled')
        total_additions = sum(c['additions'] for c in commits)
        total_deletions = sum(c['deletions'] for c in commits)

        lines.extend([
            f"**Thesis**: {title}",
            f"**Period**: Last {days} days",
            f"**Commits**: {len(commits)}",
            f"**Changes**: +{total_additions} / -{total_deletions} lines\n",
            "### Commits\n",
        ])

        # Add commit details from base report (extract the commits section)
        # Split base report and get commits section
        if "### Commits" in base_report:
            commits_section = base_report.split("### Commits\n", 1)[1]
            lines.append(commits_section)

        return "\n".join(lines)

    def _get_progress_emoji(self, score: int) -> str:
        """Get emoji indicator for progress score."""
        if score >= 9:
            return "🟢"  # Excellent
        elif score >= 7:
            return "🟡"  # Good
        elif score >= 5:
            return "🟠"  # Moderate
        else:
            return "🔴"  # Concerning

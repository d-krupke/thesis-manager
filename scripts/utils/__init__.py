"""
Utility modules for GitLab Weekly Reporter.

This package contains modular components for the reporting system:
- gitlab_client: GitLab API interactions
- thesis_manager_client: Thesis Manager API interactions
- report_generator: Report generation (base class)
- ai_report_generator: AI-enhanced report generation
"""

from .gitlab_client import GitLabClient
from .thesis_manager_client import ThesisManagerClient
from .report_generator import ReportGenerator
from .ai_report_generator import AIReportGenerator, ProgressAnalysis

__all__ = [
    'GitLabClient',
    'ThesisManagerClient',
    'ReportGenerator',
    'AIReportGenerator',
    'ProgressAnalysis',
]

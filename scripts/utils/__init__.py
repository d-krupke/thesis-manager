"""
Utility modules for GitLab Weekly Reporter.

This package contains modular components for the reporting system:
- gitlab_client: GitLab API interactions
- thesis_manager_client: Thesis Manager API interactions
- report_generator: Report generation (extensible for AI)
"""

from .gitlab_client import GitLabClient
from .thesis_manager_client import ThesisManagerClient
from .report_generator import ReportGenerator

__all__ = ['GitLabClient', 'ThesisManagerClient', 'ReportGenerator']

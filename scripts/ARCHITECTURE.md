# GitLab Reporter Architecture

## Overview

The GitLab Reporter has been refactored into a modular architecture for better maintainability and extensibility, particularly for future AI enhancements.

## File Structure

```
scripts/
├── gitlab_reporter.py          # Main orchestration script (243 lines)
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (not in git)
├── README.md                   # User documentation
├── ARCHITECTURE.md            # This file
└── utils/                      # Utility modules
    ├── __init__.py             # Package initialization
    ├── gitlab_client.py        # GitLab API client
    ├── thesis_manager_client.py # Thesis Manager API client
    └── report_generator.py     # Report generation (extensible)
```

## Module Descriptions

### `gitlab_reporter.py` (Main Script)

**Purpose**: Orchestrates the workflow

**Responsibilities**:
- Command-line argument parsing
- Logging configuration
- Client initialization
- Processing coordination
- Error handling and reporting

**Key Functions**:
- `process_thesis()`: Processes a single thesis
- `main()`: Entry point and workflow coordination

**Lines**: ~243 (down from ~714)

---

### `utils/gitlab_client.py`

**Purpose**: Handles all GitLab API interactions

**Responsibilities**:
- GitLab authentication and connection
- Project discovery from URLs
- Commit history retrieval
- Diff analysis and file change tracking
- Branch scanning

**Key Methods**:
- `get_project_by_path()`: Get project by path
- `extract_project_path_from_url()`: Parse repository URLs
- `collect_recent_commits()`: Fetch commits from all branches
- `_parse_diff_files()`: Extract file changes from diffs

**Dependencies**: `python-gitlab`, `os`, `re`, `logging`

---

### `utils/thesis_manager_client.py`

**Purpose**: Handles Thesis Manager REST API interactions

**Responsibilities**:
- Knox token authentication
- Fetching theses by phase/status
- Creating automated comments
- Two-stage thesis fetching (list → details)

**Key Methods**:
- `get_active_theses()`: Fetch working theses with repositories
- `get_thesis_by_id()`: Fetch full thesis details
- `create_comment()`: Post automated report comments

**Strategy**: Uses two-stage fetch to avoid modifying list serializer:
1. Fetch list (has `phase`, no `git_repository`)
2. Filter for "working" phase
3. Fetch details for each (has `git_repository`)
4. Keep only those with repos

**Dependencies**: `requests`, `os`, `logging`

---

### `utils/report_generator.py`

**Purpose**: Generate reports from commit data

**Responsibilities**:
- Format commit data into markdown reports
- Calculate statistics (commits, authors, changes)
- Generate activity summaries
- Handle no-activity cases

**Key Methods**:
- `generate_report()`: Main entry point
- `_generate_activity_report()`: Report with commits
- `_generate_no_activity_report()`: Report when no activity

**Extensibility**: Base class designed for AI enhancement:
```python
class AIReportGenerator(ReportGenerator):
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate_report(self, commits, thesis, days):
        basic = super().generate_report(commits, thesis, days)
        insights = self.llm.analyze(commits, thesis)
        return f"{basic}\n\n{insights}"
```

**Dependencies**: `logging`, `typing`

---

## Data Flow

```
1. Main Script (gitlab_reporter.py)
   ↓
2. ThesisManagerClient.get_active_theses()
   → Fetch working theses with repositories
   ↓
3. For each thesis:
   ├─ GitLabClient.extract_project_path_from_url()
   │  → Parse repository URL
   ├─ GitLabClient.get_project_by_path()
   │  → Get GitLab project
   ├─ GitLabClient.collect_recent_commits()
   │  → Fetch commits from all branches
   ├─ ReportGenerator.generate_report()
   │  → Create markdown report
   └─ ThesisManagerClient.create_comment()
      → Post comment to thesis
```

## Benefits of Refactoring

### 1. **Maintainability**
- Each module has a single, clear responsibility
- Easier to locate and fix bugs
- Reduced cognitive load when reading code

### 2. **Testability**
- Modules can be tested independently
- Easy to mock dependencies
- Clear interfaces between components

### 3. **Extensibility**
- Can subclass `ReportGenerator` for AI features
- Can add new clients without touching existing code
- Modules can be reused in other scripts

### 4. **Readability**
- Main script is now ~243 lines vs ~714
- Clear separation of concerns
- Better documentation structure

## Design Patterns Used

### 1. **Client Pattern**
- `GitLabClient` and `ThesisManagerClient` encapsulate API interactions
- Hides implementation details from main script
- Makes testing easier (can mock clients)

### 2. **Strategy Pattern** (Preparatory)
- `ReportGenerator` as base class
- Allows switching report generation strategies
- Enables future AI-enhanced generators

### 3. **Facade Pattern**
- `utils/__init__.py` provides simple imports
- Hides internal module structure
- Clean interface: `from utils import GitLabClient`

## Logging Architecture

All modules use Python's `logging` module with consistent patterns:

```python
logger = logging.getLogger(__name__)
```

**Logging Levels**:
- `INFO`: Key operations (thesis processing, API calls)
- `DEBUG`: Detailed information (enabled with --verbose)
- `WARNING`: Recoverable issues
- `ERROR`: Failures

**Format**: `%(asctime)s - %(levelname)s - %(message)s`

**Style**: Printf-style formatting for efficiency
```python
logger.info("Processing %d theses", count)  # Good
logger.info(f"Processing {count} theses")   # Avoid
```

## Configuration

All configuration via environment variables (`.env` file):

```bash
# GitLab
GITLAB_URL=https://gitlab.ibr.cs.tu-bs.de/
GITLAB_TOKEN=your-token

# Thesis Manager
THESIS_MANAGER_URL=https://thesis-manager.example.com/
THESIS_MANAGER_API_TOKEN=your-knox-token
```

**Security**: `.env` file not committed to git

## Future Enhancements

### AI Integration (Planned)

Create `utils/ai_report_generator.py`:

```python
from .report_generator import ReportGenerator

class AIReportGenerator(ReportGenerator):
    """AI-enhanced report generator using LLMs."""

    def __init__(self, llm_client):
        self.llm = llm_client

    def generate_report(self, commits, thesis, days):
        # Get base report
        base = super().generate_report(commits, thesis, days)

        # Add AI analysis
        if commits:
            analysis = self._analyze_with_ai(commits, thesis)
            return f"{base}\n\n### AI Analysis\n\n{analysis}"
        return base

    def _analyze_with_ai(self, commits, thesis):
        """Use LLM to analyze commit patterns."""
        prompt = self._build_analysis_prompt(commits)
        return self.llm.complete(prompt)
```

Update main script:
```python
# In main()
if use_ai:
    report_gen = AIReportGenerator(anthropic_client)
else:
    report_gen = ReportGenerator()
```

### Additional Modules (Ideas)

- `utils/commit_analyzer.py`: Statistical analysis of commits
- `utils/notification_manager.py`: Handle email/Slack notifications
- `utils/cache_manager.py`: Cache GitLab API responses
- `utils/metrics_tracker.py`: Track script performance

## Dependencies

See `requirements.txt`:
- `python-gitlab>=4.0.0`: GitLab API client
- `requests>=2.31.0`: HTTP requests for Thesis Manager API
- `python-dotenv>=1.0.0`: Environment variable management

## Testing

To test the refactored structure:

```bash
# Test imports
python -c "from utils import GitLabClient, ThesisManagerClient, ReportGenerator"

# Test script help
python gitlab_reporter.py --help

# Dry run test
python gitlab_reporter.py --dry-run --verbose
```

## Migration Notes

**Before**: Single file with 714 lines containing all logic

**After**: Modular structure with:
- Main script: 243 lines (66% reduction)
- GitLabClient: ~200 lines
- ThesisManagerClient: ~210 lines
- ReportGenerator: ~100 lines
- Total: ~753 lines (slightly more due to module headers/imports)

**Trade-off**: Slightly more lines overall, but significantly better organization and maintainability.

## Version History

- **v1.0**: Initial monolithic script
- **v2.0**: Refactored to modular architecture (current)
- **v3.0** (planned): AI-enhanced report generation

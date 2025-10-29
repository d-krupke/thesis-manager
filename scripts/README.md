# GitLab Reporter Scripts

Automated reporting tools for tracking student thesis progress via GitLab repository activity.

## Overview

The `gitlab_reporter.py` script automatically analyzes GitLab repositories for active theses and generates weekly activity reports that are posted as comments to the Thesis Manager system.

## Architecture

The script is designed with modularity and extensibility in mind, particularly for future AI enhancement:

### Components

1. **GitLabClient** (`gitlab_reporter.py:52`)
   - Handles all GitLab API interactions
   - Fetches commit data, diffs, and statistics
   - Parses repository URLs to extract project paths
   - Methods: `get_project_by_path()`, `collect_recent_commits()`, `extract_project_path_from_url()`

2. **ThesisManagerClient** (`gitlab_reporter.py:232`)
   - Handles Thesis Manager REST API interactions
   - Uses Knox token authentication
   - Fetches active theses and creates comments
   - Methods: `get_active_theses()`, `get_thesis_by_id()`, `create_comment()`

3. **ReportGenerator** (`gitlab_reporter.py:354`)
   - **Base class for report generation** - designed for extension
   - Currently generates simple markdown-formatted reports
   - Can be subclassed to create AI-enhanced report generators
   - Methods: `generate_report()`, `_generate_activity_report()`, `_generate_no_activity_report()`

4. **Main Orchestrator** (`gitlab_reporter.py:451`)
   - Coordinates the workflow
   - Processes each thesis: fetch commits → generate report → post comment
   - Function: `process_thesis()`, `main()`

## Setup

### 1. Install Dependencies

```bash
# Activate your conda environment
conda activate web312

# Install required packages
pip install -r scripts/requirements.txt
```

### 2. Configure Environment Variables

The script requires the following environment variables in `scripts/.env`:

```bash
# GitLab Configuration
GITLAB_URL=https://gitlab.ibr.cs.tu-bs.de/
GITLAB_TOKEN=your-gitlab-token-here

# Thesis Manager Configuration
THESIS_MANAGER_URL=https://your-thesis-manager.com/
THESIS_MANAGER_API_TOKEN=your-knox-token-here

# OpenAI Configuration (optional - for AI-enhanced reporting)
OPENAI_API_KEY=sk-...
```

### 3. GitLab Token Requirements

Your GitLab token needs at least `read_repository` scope to access:
- Commit history
- Diff information
- Branch information

## Usage

### Basic Usage

```bash
# Process all active theses (not completed/abandoned) with repositories
python gitlab_reporter.py

# Test with a specific thesis
python gitlab_reporter.py --thesis-id 5

# Dry run (preview without creating comments)
python gitlab_reporter.py --dry-run

# Custom time period (default: 7 days)
python gitlab_reporter.py --days 14

# Enable AI-powered progress analysis
python gitlab_reporter.py --ai

# AI with specific model (default: gpt-4o-mini)
python gitlab_reporter.py --ai --ai-model gpt-4o
```

### AI-Enhanced Reporting

When the `--ai` flag is enabled, the script uses ChatGPT to analyze commit activity and provide intelligent insights:

**AI Analysis Includes:**
- **Summary**: Concise 3-sentence summary of progress
- **Code Progress Score**: 0-10 rating of implementation progress
- **Thesis Progress Score**: 0-10 rating of thesis writing progress (LaTeX files)
- **Attention Flag**: Alerts when progress is concerning
- **Reasoning**: Brief explanation of scores

**Example AI-Enhanced Report:**
```markdown
## Weekly Repository Activity Report

### 🤖 AI Progress Analysis

⚠️ **Attention Required**

The student made minimal progress this week with only 2 commits
focused on documentation. No substantive code changes were detected.
With the deadline in 45 days, more consistent implementation work
is needed.

**Progress Scores:**
- Implementation: **3/10** 🔴
- Thesis Writing: **5/10** 🟠

*Low code activity and approaching deadline warrant supervisor attention.*
```

**Configuration:**
- Requires `OPENAI_API_KEY` in `.env`
- Uses `gpt-4o-mini` by default (cost-efficient)
- Can specify model with `--ai-model` flag
- Gracefully falls back to basic reporting if API unavailable

**Audit Logging:**
- All AI interactions are logged to `scripts/logs/ai_audit.log`
- Logs include: complete context sent to OpenAI, AI responses, consent denials
- Use for transparency, debugging, and compliance
- See [AI_FEATURES.md](AI_FEATURES.md#audit-logging) for details

### Scheduled Execution

You can run this script via cron or systemd timer for weekly reports:

```cron
# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/thesis-manager/scripts && /path/to/conda/envs/web312/bin/python gitlab_reporter.py
```

## Report Format

The generated reports include:

- **Summary Statistics**: Total commits, authors, lines changed
- **Individual Commits**: Commit SHA, message, author, timestamp, statistics
- **File Changes**: Changed files with status indicators (new, renamed, deleted)
- **Branch Information**: Which branches contain each commit

Example report output:
```markdown
## Weekly Repository Activity Report

**Thesis**: Example Thesis Title
**Period**: Last 7 days
**Commits**: 6
**Authors**: Student Name
**Changes**: +521 / -209 lines

### Commits

**8812d47c** - Implemented parallel cell solving
*Student Name* | 2025-10-27 12:02 | +144/-127 lines | branches: dev

Files changed:
  - `src/main.rs`
  - `src/solver.rs`
```

## Extending with AI

### Current Design Decisions

The architecture was designed to make AI integration straightforward:

1. **Separation of Concerns**: Data fetching (GitLabClient), data formatting (ReportGenerator), and integration (ThesisManagerClient) are separate
2. **Base Class Pattern**: `ReportGenerator` is designed to be subclassed
3. **Rich Data Structure**: Commits are collected with full metadata (files, diffs, stats)

### Future AI Enhancement Options

#### Option 1: Subclass ReportGenerator

Create an `AIReportGenerator` that extends `ReportGenerator`:

```python
class AIReportGenerator(ReportGenerator):
    """
    AI-enhanced report generator using LLM to analyze commits.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client  # e.g., OpenAI, Anthropic, etc.

    def generate_report(self, commits, thesis, days):
        # Get basic report from parent class
        basic_report = super().generate_report(commits, thesis, days)

        if not commits:
            return basic_report

        # Use LLM to analyze commits and add insights
        ai_insights = self._generate_ai_insights(commits, thesis)

        # Combine basic report with AI insights
        return f"{basic_report}\n\n{ai_insights}"

    def _generate_ai_insights(self, commits, thesis):
        """
        Use LLM to analyze commit patterns and generate insights.

        Potential analyses:
        - Progress assessment (is student on track?)
        - Code quality signals (commit message quality, file organization)
        - Risk indicators (no activity, too many deletions)
        - Suggested next steps or questions for supervisor
        """
        prompt = self._build_analysis_prompt(commits, thesis)
        return self.llm_client.complete(prompt)
```

Then update main() to use it:
```python
# In main():
report_gen = AIReportGenerator(llm_client=anthropic_client)
```

#### Option 2: Add AI Analysis as Separate Step

Keep the base reporter, add AI analysis as a post-processing step:

```python
def add_ai_analysis(report, commits, thesis, llm_client):
    """Add AI-generated insights to existing report."""
    analysis = llm_client.analyze(commits=commits, thesis=thesis)
    return f"{report}\n\n---\n\n### AI Analysis\n\n{analysis}"
```

#### Option 3: Hybrid Approach

Generate both simple and AI-enhanced reports, allowing supervisors to choose:

```python
# Simple report (auto-generated comment)
simple_report = ReportGenerator().generate_report(commits, thesis, days)
tm_client.create_comment(thesis_id, simple_report, is_auto_generated=True)

# AI-enhanced report (separate comment or attachment)
if enable_ai:
    ai_report = AIReportGenerator(llm).generate_report(commits, thesis, days)
    tm_client.create_comment(thesis_id, ai_report, is_auto_generated=True)
```

### Recommended AI Features

When adding AI functionality, consider:

1. **Progress Assessment**: Is the student making adequate progress?
2. **Risk Detection**: Warning signs (no activity, chaotic commits, no test updates)
3. **Quality Indicators**: Commit message quality, code organization signals
4. **Contextual Questions**: Generate specific questions for supervisor review
5. **Trend Analysis**: Compare current week to previous weeks
6. **Code Complexity Analysis**: Parse diffs to assess complexity changes

### Data Available for AI Analysis

The `commits` list contains rich data for each commit:
- `sha`, `short`: Commit identifiers
- `title`: Commit message
- `author`, `email`: Author information
- `date`: Timestamp
- `additions`, `deletions`: Line changes
- `files`: List of changed files with status (new, renamed, deleted)
- `branches`: Branches containing this commit

## Troubleshooting

### Common Issues

**No theses found**:
- Check that theses have `git_repository` field populated
- Verify theses are not in 'completed' or 'abandoned' phase
- Test with `--thesis-id` flag for specific thesis

**GitLab authentication fails**:
- Verify `GITLAB_TOKEN` has correct permissions
- Check token hasn't expired
- Ensure URL matches your GitLab instance

**Cannot access repository**:
- Verify GitLab token has access to the project
- Check repository URL is correctly formatted
- Ensure project hasn't been archived or deleted

**Thesis Manager API errors**:
- Verify `THESIS_MANAGER_API_TOKEN` is valid Knox token
- Check user permissions (needs ability to create comments)
- Test API access manually: `curl -H "Authorization: Token $TOKEN" $URL/api/theses/`

## Development

### Testing

```bash
# Test without creating comments
python gitlab_reporter.py --dry-run

# Test specific thesis
python gitlab_reporter.py --thesis-id 1 --dry-run

# Test with shorter period
python gitlab_reporter.py --days 1 --dry-run
```

### Adding New Features

1. Keep separation of concerns (GitLab logic in GitLabClient, etc.)
2. Update type hints for new methods
3. Add error handling with graceful degradation
4. Test with `--dry-run` before production use
5. Consider backwards compatibility

## License

This script is part of the Thesis Manager project. See parent repository for license information.

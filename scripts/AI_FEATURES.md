# AI-Enhanced Progress Analysis

## Overview

The GitLab Reporter now includes optional AI-powered progress analysis using ChatGPT via pydantic-ai. This provides intelligent insights into student thesis progress.

## Privacy and Consent

### Per-Thesis AI Control

Each thesis has two privacy-related fields:

1. **`ai_summary_enabled`** (boolean, default: `True`)
   - Controls whether AI analysis is performed for this thesis
   - Disable if student does not consent to external AI processing
   - When disabled, reports fall back to basic commit summaries
   - Logged: `"AI analysis disabled for thesis #X (student consent not given)"`

2. **`ai_context`** (text, max 500 characters)
   - Provides additional context to the AI for more accurate analysis
   - Examples:
     - "Pure theory thesis, no implementation expected"
     - "Focus on hardware development, code changes will be minimal"
     - "Student is working on documentation first, code comes later"
   - Helps AI avoid false negatives (e.g., flagging theory thesis for no code)

### Data Privacy

What gets sent to OpenAI:
- Commit metadata (dates, messages, authors)
- File paths and change statistics
- Thesis title and timeline information
- Custom context (if provided)

What does NOT get sent:
- Actual code content
- File contents
- Personal identifying information beyond names/emails in commits
- Any sensitive data from repository

### Configuration

Set these fields via:
- **Web interface**: Edit thesis form (new "AI-Enhanced Reporting Settings" section)
- **Django admin**: Thesis edit page (collapsible section at bottom)
- **REST API**: Include in thesis creation/update:
  ```json
  {
    "ai_summary_enabled": false,
    "ai_context": "Theory thesis focusing on algorithmic analysis"
  }
  ```

## Features

### Structured Analysis with Pydantic

Uses `ProgressAnalysis` model for type-safe, structured output:

```python
class ProgressAnalysis(BaseModel):
    summary: str                    # 3-sentence summary
    code_progress_score: int        # 0-10 rating
    thesis_progress_score: int      # 0-10 rating
    needs_attention: bool           # Alert flag
    reasoning: str                  # Explanation
```

### What the AI Analyzes

1. **Commit Activity**
   - Frequency and consistency
   - Total changes (additions/deletions)
   - Commit message quality

2. **File Types**
   - Code files (.py, .java, .cpp, .rs, etc.)
   - Thesis files (.tex, .bib, .md)
   - Documentation updates

3. **Timeline Context**
   - Days since registration
   - Days until deadline
   - Expected progress trajectory

4. **Progress Scoring**
   - **Code Progress (0-10)**:
     - 0-2: No meaningful changes
     - 3-4: Minimal, concerning
     - 5-6: Some progress
     - 7-8: Good, steady progress
     - 9-10: Excellent progress

   - **Thesis Progress (0-10)**:
     - Based on LaTeX/documentation changes
     - Similar scale to code progress

5. **Attention Flag**
   - Triggered by:
     - Very low activity near deadline
     - No progress for extended period
     - Concerning patterns (last-minute only)

## Usage

### Enable AI Analysis

```bash
# Basic AI-enhanced reporting
python gitlab_reporter.py --ai

# With specific model
python gitlab_reporter.py --ai --ai-model gpt-4o

# Test with dry-run
python gitlab_reporter.py --thesis-id 1 --ai --dry-run
```

### Configuration

Add to `scripts/.env`:
```bash
OPENAI_API_KEY=sk-...
```

### Example Output

```markdown
## Weekly Repository Activity Report

### 🤖 AI Progress Analysis

⚠️ **Attention Required**

The student made significant implementation progress with 6 commits
adding 521 lines of code across core solver modules. However, no
thesis writing activity was detected. With 45 days until deadline,
LaTeX writing should begin soon.

**Progress Scores:**
- Implementation: **8/10** 🟡
- Thesis Writing: **2/10** 🔴

*Good code progress but thesis writing needs to start.*

---

**Thesis**: Example Thesis
**Period**: Last 7 days
**Commits**: 6
**Authors**: Student Name
**Changes**: +521 / -209 lines

### Commits
...
```

## Architecture

### Class Hierarchy

```
ReportGenerator (base class)
    ├── generate_report()
    └── _generate_activity_report()

AIReportGenerator (extends ReportGenerator)
    ├── __init__(api_key, model)
    ├── generate_report()          # Overrides with AI
    ├── _analyze_progress()        # AI analysis
    ├── _build_analysis_context()  # Context preparation
    └── _format_enhanced_report()  # Enhanced formatting
```

### Pydantic-AI Integration

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Initialize agent
model = OpenAIModel('gpt-4o-mini', api_key=api_key)
agent = Agent(
    model,
    result_type=ProgressAnalysis,
    system_prompt=...
)

# Run analysis
result = agent.run_sync(context)
analysis = result.data  # ProgressAnalysis instance
```

### System Prompt

The AI is given expert thesis supervisor persona with instructions to:
- Analyze commit patterns holistically
- Consider timeline context
- Be realistic but encouraging
- Flag issues early for student success
- Provide actionable insights

## Benefits

### For Supervisors

1. **Quick Overview**: Instant understanding of progress
2. **Early Warnings**: Automatic flagging of concerns
3. **Objective Metrics**: Consistent 0-10 scoring
4. **Context Aware**: Considers deadlines and timelines
5. **Time Saving**: No manual commit review needed

### For Students

1. **Regular Feedback**: Weekly progress assessment
2. **Clear Metrics**: Know where they stand
3. **Actionable**: Identifies areas needing attention
4. **Motivating**: Recognition of good progress

## Cost Considerations

### Token Usage

Typical request:
- **Input**: ~500-1000 tokens (commit data + context)
- **Output**: ~200-300 tokens (structured analysis)
- **Total**: ~700-1300 tokens per thesis

### Model Recommendations

**Default: gpt-4o-mini**
- Cost: $0.15/1M input tokens, $0.60/1M output tokens
- ~$0.0001-0.0002 per thesis analysis
- Excellent quality/cost ratio

**Alternative: gpt-4o**
- Cost: $2.50/1M input tokens, $10/1M output tokens
- ~$0.002-0.003 per thesis analysis
- Slightly better quality

**Budget Example:**
- 20 theses × weekly reports × 4 weeks = 80 reports/month
- With gpt-4o-mini: ~$0.01-0.02/month
- With gpt-4o: ~$0.16-0.24/month

## Fallback Behavior

AI analysis gracefully degrades:

1. **No API Key**: Logs warning, uses basic reporting
2. **API Error**: Catches exception, falls back to basic
3. **No Commits**: Skips AI analysis (not needed)
4. **Network Issues**: Logs error, continues with basic

Users always get a report, even if AI fails.

## Technical Details

### Dependencies

```txt
pydantic-ai>=0.0.14     # AI agent framework
openai>=1.0.0           # OpenAI API client
pydantic>=2.0.0         # Data validation
```

### Key Files

- `utils/ai_report_generator.py`: AIReportGenerator class
- `utils/report_generator.py`: Base ReportGenerator
- `gitlab_reporter.py`: Main script with --ai flag

### Logging

```python
logger.info("AI-enhanced reporting enabled with model: gpt-4o-mini")
logger.debug("Running AI analysis for thesis #1")
logger.debug("AI analysis complete: score=8/2, attention=True")
```

## Future Enhancements

### Potential Additions

1. **Historical Comparison**: Compare to previous weeks
2. **Peer Benchmarking**: Compare to similar theses
3. **Predictive Analysis**: Likelihood of on-time completion
4. **Personalized Feedback**: Student-specific suggestions
5. **Multilingual Support**: Analysis in multiple languages

### Alternative Models

- **Claude (Anthropic)**: Via pydantic-ai
- **Gemini (Google)**: Via pydantic-ai
- **Local Models**: Ollama integration

## Testing

```bash
# Test AI analysis
python gitlab_reporter.py --thesis-id 1 --ai --dry-run --verbose

# Test fallback
unset OPENAI_API_KEY
python gitlab_reporter.py --thesis-id 1 --ai --dry-run

# Test different models
python gitlab_reporter.py --thesis-id 1 --ai --ai-model gpt-4o --dry-run
```

## Security

### API Key Storage

- Store in `.env` file (not in git)
- Environment variable only
- Never log or print API keys

### Data Privacy

- Only sends: commit metadata, file names, dates
- Does NOT send: actual code, file contents, personal data
- Thesis title and phase sent for context

### Rate Limiting

- pydantic-ai handles OpenAI rate limits
- Automatic retry with exponential backoff
- Error handling for quota exceeded

## Monitoring

### Success Metrics

Track:
- AI analysis success rate
- Average analysis time
- Cost per analysis
- Supervisor feedback on usefulness

### Error Monitoring

Log:
- API failures
- Timeout issues
- Invalid responses
- Fallback activations

## Documentation

- Main README: Basic usage and examples
- ARCHITECTURE.md: Technical design
- AI_FEATURES.md: This document (detailed AI features)

## Support

For issues with AI features:
1. Check `OPENAI_API_KEY` is set correctly
2. Verify API key has credits
3. Check logs with `--verbose` flag
4. Test with `--dry-run` first
5. Verify pydantic-ai version compatibility

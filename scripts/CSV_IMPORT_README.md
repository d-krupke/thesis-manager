# CSV Import Tool for Thesis Manager

This tool uses a PydanticAI agent to intelligently import thesis data from CSV files into the Thesis Manager system. It handles non-uniform data, fuzzy matching of existing records, and provides interactive confirmation at each step.

## Features

- **Intelligent Parsing**: Uses AI (Claude) to extract structured data from messy CSV rows
- **Fuzzy Matching**: Automatically finds existing students, supervisors, and theses
- **Duplicate Detection**: Warns about potential duplicate theses before creation
- **Interactive Mode**: Confirms each action before making changes
- **Dry Run Mode**: Analyze CSV without making any changes
- **Resume Support**: Start from any row number
- **German Data Support**: Handles German column names and date formats

## Installation

1. Install the required dependencies:

```bash
cd scripts
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
export THESIS_MANAGER_URL="http://localhost"
export THESIS_MANAGER_API_TOKEN="your-api-token-here"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or create a `.env` file in the scripts directory:

```
THESIS_MANAGER_URL=http://localhost
THESIS_MANAGER_API_TOKEN=your-token
ANTHROPIC_API_KEY=your-key
```

## Usage

### Basic Usage

```bash
./import_csv.py path/to/theses.csv
```

This will run in interactive mode, asking for confirmation at each step.

### Dry Run (Analyze Only)

```bash
./import_csv.py path/to/theses.csv --dry-run
```

This will parse and analyze the CSV without making any changes to the database.

### Non-Interactive Mode

```bash
./import_csv.py path/to/theses.csv --non-interactive
```

This will use default choices and create new records automatically without asking for confirmation.

### Start from Specific Row

```bash
./import_csv.py path/to/theses.csv --start-from 10
```

Useful if the import was interrupted or if you want to skip already-imported rows.

### Using Different Model

```bash
./import_csv.py path/to/theses.csv --model claude-3-opus-20240229
```

Uses a different Claude model for parsing (default is claude-3-5-sonnet-20241022).

## CSV Format

The tool expects a CSV with the following German column names:

| Column | Description | Required |
|--------|-------------|----------|
| `Name` | Student's last name | Yes |
| `Vorname` | Student's first name | Yes |
| `Email-Adresse` | Student's email | No |
| `Matr. Nr.` | Matriculation number | No |
| `B/M/P` | Thesis type (B=Bachelor, M=Master, P=Project) | Yes |
| `Thema` | Thesis title/topic | No |
| `Erstkontakt` | First contact date | No |
| `Anmeldung Datum` | Registration date | No |
| `Abgabe Datum` | Submission deadline | No |
| `abgegeben am` | Actual submission date | No |
| `Vortrag am` | Presentation date | No |
| `Aufgabenst. u. Betreuer` | Task description and supervisor | No |
| `Betreuer WMA` | Supervisor WMA | No |
| `Zweitgutachter` | Second reviewer | No |
| `Studiengang` | Degree program | No |
| `Semesterzahl` | Semester count | No |
| `Note` | Final grade | No |
| `Noten` | Notes/grades | No |
| `Literatur-Recherche` | Literature research notes | No |
| `Besch. 4,0 + Vortr.` | Description | No |

## How It Works

The import process follows these steps for each CSV row:

### 1. **Parsing** (AI-powered)
- The agent extracts structured data from the CSV row
- Handles missing data, various date formats, and free-text fields
- Identifies supervisors from text fields
- Infers thesis phase from available dates

### 2. **Student Matching**
- Searches for existing students by email (exact match)
- Falls back to fuzzy name matching if no email match
- Checks matriculation number for exact match
- Suggests similar students for confirmation
- Creates new student if no match found

### 3. **Supervisor Matching**
- Searches for existing supervisors by email (exact match)
- Falls back to fuzzy name matching
- Can extract multiple supervisors from text fields
- Suggests similar supervisors for confirmation
- Creates new supervisors if no match found

### 4. **Duplicate Detection**
- Searches for existing theses with:
  - Same thesis type (bachelor/master/project)
  - Same student(s)
  - Similar title (optional)
- Warns if potential duplicate found
- Allows user to decide whether to continue

### 5. **Thesis Creation**
- Creates thesis with all extracted information
- Links to student(s) and supervisor(s)
- Sets appropriate phase based on dates
- Includes all metadata in description

## Matching Logic

### Fuzzy Matching Thresholds
- **Email**: Exact match (case-insensitive) = 100% confidence
- **Names**: Uses SequenceMatcher with 80% default threshold
- **Student ID**: Exact match = 100% confidence
- **Thesis**: Requires same type + student overlap, title similarity is optional

### Phase Inference
The agent automatically infers the thesis phase from available dates:
- If grade is present → `completed`
- If presentation date is present → `defended`
- If submission date is present → `submitted`
- If registration date is present → `registered` or `working`
- If only first contact date → `first_contact`
- If data looks abandoned → `abandoned`

## Example Session

```
THESIS MANAGER CSV IMPORT TOOL
================================================================================
CSV File: theses.csv
Mode: INTERACTIVE
Model: claude-3-5-sonnet-20241022
================================================================================
✅ Connected to Thesis Manager API
✅ Initialized import agent
✅ Read 25 rows from CSV

================================================================================
PROCESSING 25 ROWS
================================================================================

================================================================================
ROW 2: Max Mustermann
================================================================================

📋 PARSED DATA:
  Student: Max Mustermann (max.mustermann@example.com) [ID: 12345]
  Type: bachelor
  Title: Efficient Algorithms for Graph Processing
  Phase: completed
  Supervisors: 1
    1. Prof. Dr. Schmidt (schmidt@uni.de) [primary supervisor]

--------------------------------------------------------------------------------
STEP 1: STUDENT
--------------------------------------------------------------------------------
✅ Found exact match: Max Mustermann (ID: 42)
Use this student? [Y/n]: y
✅ Using student ID: 42

--------------------------------------------------------------------------------
STEP 2: SUPERVISORS
--------------------------------------------------------------------------------

Supervisor 1/1: Prof. Dr. Schmidt (schmidt@uni.de) [primary supervisor]

🔍 Similar supervisors found:
  Prof. Dr. Peter Schmidt (p.schmidt@uni.de) - 95% match
  Prof. Dr. Anna Schmidt (a.schmidt@uni.de) - 80% match

Which supervisor to use?
  1. Prof. Dr. Peter Schmidt (p.schmidt@uni.de)
  2. Prof. Dr. Anna Schmidt (a.schmidt@uni.de)
  0. Skip / Create new
Choose [1-2 or 0]: 1
✅ Using supervisor ID: 15

--------------------------------------------------------------------------------
STEP 3: CHECK FOR DUPLICATES
--------------------------------------------------------------------------------
✅ No similar theses found

--------------------------------------------------------------------------------
STEP 4: CREATE THESIS
--------------------------------------------------------------------------------

📝 Ready to create:
  Type: bachelor
  Title: Efficient Algorithms for Graph Processing
  Student ID: 42
  Supervisor IDs: [15]
  Phase: completed

Create this thesis? [Y/n]: y
Creating thesis...
✅ Created thesis ID: 128

[... continues for remaining rows ...]

================================================================================
IMPORT SUMMARY
================================================================================
✅ Successful: 23
⏭️  Skipped: 1
❌ Errors: 1
Total processed: 25 / 25
================================================================================
```

## Adapting for Your Needs

### Using as a Library

You can import and use the components in your own scripts:

```python
from utils.thesis_manager_client import ThesisManagerClient
from utils.csv_import_tool import CSVImportTool
from thesis_csv_import_agent import ThesisCSVImportAgent

# Initialize
client = ThesisManagerClient()
agent = ThesisCSVImportAgent(client)

# Read and parse CSV
rows = agent.read_csv_file("data.csv")

# Process individual rows
for row in rows:
    parsed = await agent.parse_csv_row(row)
    # ... handle parsed data ...
```

### Customizing the Parser

The parser agent's system prompt can be modified in `thesis_csv_import_agent.py`:

```python
def _get_parser_system_prompt(self) -> str:
    return """Your custom instructions here..."""
```

### Adjusting Matching Thresholds

Thresholds can be adjusted in `matching.py`:

```python
# Default is 0.8 (80% similarity)
matches = match_student(..., threshold=0.9)  # Stricter
matches = match_student(..., threshold=0.7)  # More lenient
```

## Troubleshooting

### API Connection Errors

```
❌ ERROR: Failed to connect to API: THESIS_MANAGER_URL not set in environment
```

**Solution**: Set the environment variables or pass them as arguments:
```bash
./import_csv.py data.csv --url http://localhost --token your-token
```

### Parsing Errors

If the agent fails to parse a row, check:
1. Is the `ANTHROPIC_API_KEY` set correctly?
2. Are the CSV column names correct (case-sensitive)?
3. Is the row completely empty?

Use `--dry-run` to see parsing results without making changes.

### Duplicate Detection Too Aggressive

If too many false positives for duplicates:
- Increase the `title_threshold` in `find_similar_theses()`
- Or adjust the matching logic in `matching.py`

### Missing Required Fields

The tool handles missing data gracefully:
- Missing student email → generates placeholder email
- Missing supervisor email → generates placeholder email
- Missing thesis title → uses "Untitled"
- Missing dates → left as None

## Architecture

```
import_csv.py (CLI)
    ↓
thesis_csv_import_agent.py (PydanticAI Agent)
    ↓
csv_import_tool.py (Business Logic)
    ↓
thesis_manager_client.py (API Client)
    ↓
matching.py (Fuzzy Matching)

csv_import_models.py (Data Models)
```

### Key Components

- **`import_csv.py`**: CLI interface with interactive prompts
- **`thesis_csv_import_agent.py`**: PydanticAI agent for intelligent parsing
- **`csv_import_tool.py`**: Core business logic for import operations
- **`thesis_manager_client.py`**: API client with CRUD operations
- **`matching.py`**: Fuzzy matching utilities
- **`csv_import_models.py`**: Pydantic models for data validation

## Future Enhancements

Possible improvements:
- Support for updating existing records (not just creating)
- Batch processing for better performance
- More sophisticated duplicate detection (ML-based)
- Custom field mapping for different CSV formats
- Export functionality (database → CSV)
- Validation rules for data quality
- Rollback functionality for failed imports

## License

Same license as the Thesis Manager project.

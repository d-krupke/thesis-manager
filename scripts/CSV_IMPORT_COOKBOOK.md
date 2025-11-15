# CSV Import Agent Cookbook

A practical guide to building an AI-powered CSV import tool using PydanticAI for migrating messy thesis data.

## Table of Contents

1. [What You're Building](#what-youre-building)
2. [Core Concepts](#core-concepts)
3. [Setting Up PydanticAI](#setting-up-pydanticai)
4. [Reading Arbitrary CSV Files](#reading-arbitrary-csv-files)
5. [Using AI to Extract Structure](#using-ai-to-extract-structure)
6. [Fuzzy Matching Existing Records](#fuzzy-matching-existing-records)
7. [Interactive User Confirmation](#interactive-user-confirmation)
8. [Working with the API](#working-with-the-api)
9. [Putting It All Together](#putting-it-all-together)

---

## What You're Building

A tool that:
1. Reads a **chaotic CSV file** (varying columns, missing data, different formats)
2. Uses **AI to understand** what each row means
3. **Matches existing records** (students/supervisors) to avoid duplicates
4. **Asks the user to confirm** before creating anything
5. **Imports into Thesis Manager** via the API

**Why AI?** Because handcrafted spreadsheets are messy - different date formats, abbreviations, typos, missing data. AI can handle this chaos better than rigid parsing rules.

---

## Core Concepts

### 1. PydanticAI Agent

PydanticAI is a framework for building AI agents with **structured outputs**. Instead of getting free-form text from Claude, you get validated Python objects.

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class Person(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None

# Create an agent that returns Person objects
agent = Agent(
    model='anthropic:claude-3-5-sonnet-20241022',
    result_type=Person,  # ← AI must return this structure
    system_prompt="Extract person data from messy text"
)

# Use it
result = await agent.run("Name: John Smith, mail: j.smith@example.com")
person = result.data  # ← Validated Person object
print(person.first_name)  # "John"
```

**Key benefit:** The AI automatically figures out how to map messy input to your clean structure.

### 2. Fuzzy Matching

When importing old data, you need to detect duplicates even with slight differences:

```python
from difflib import SequenceMatcher

def similarity(s1: str, s2: str) -> float:
    """Returns 0.0 to 1.0 (1.0 = identical)"""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

# Examples
similarity("Anna Müller", "anna mueller")  # 0.91 - very similar
similarity("Prof. Schmidt", "Schmidt")     # 0.71 - somewhat similar
similarity("John Smith", "Jane Doe")       # 0.22 - different
```

Use this to find existing students/supervisors before creating new ones.

### 3. Interactive Workflow

Migration tools should **always confirm** before making changes:

```python
def ask_yes_no(question: str) -> bool:
    while True:
        response = input(f"{question} [Y/n]: ").strip().lower()
        if response in ['y', 'yes', '']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please answer y or n")

# Usage
if ask_yes_no("Create new student: Anna Müller?"):
    create_student(...)
```

---

## Setting Up PydanticAI

### Installation

```bash
pip install pydantic-ai anthropic pydantic python-dotenv
```

### Environment Setup

Create `.env` file:

```bash
THESIS_MANAGER_URL=http://localhost
THESIS_MANAGER_API_TOKEN=your-api-token
ANTHROPIC_API_KEY=your-anthropic-key
```

### Basic Agent Structure

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field

class ThesisData(BaseModel):
    """What we want to extract from each CSV row"""
    student_first_name: str
    student_last_name: str
    thesis_type: str  # bachelor/master/project
    title: str | None = None
    supervisor_names: list[str] = Field(default_factory=list)

# Create the agent
parser_agent = Agent(
    model='anthropic:claude-3-5-sonnet-20241022',
    result_type=ThesisData,
    system_prompt="""
    Extract thesis information from CSV data.
    Handle messy real-world data:
    - Varying column names (Student Name, Name, Vorname, etc.)
    - Multiple date formats
    - Abbreviations (B=Bachelor, M=Master, P=Project)
    - Multiple supervisors in one field
    - Missing data

    Be flexible and pragmatic.
    """
)
```

---

## Reading Arbitrary CSV Files

### The Challenge

You don't know the CSV structure in advance. Columns might be:
- German: `Name, Vorname, Thema, Betreuer`
- English: `Student Name, Type, Topic, Advisor`
- Mixed: `Student, B/M/P, Titel, Prof`

### Solution: Read as Raw Dictionaries

```python
import csv
from pathlib import Path

def read_csv_flexible(csv_path: Path) -> list[dict]:
    """Read CSV with any structure, return list of dicts"""
    rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Auto-detect CSV dialect (delimiter, quoting, etc.)
        sample = f.read(2048)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except:
            dialect = csv.excel()  # fallback

        reader = csv.DictReader(f, dialect=dialect)

        for i, row in enumerate(reader):
            # Clean up: remove empty values, strip whitespace
            cleaned = {
                key.strip(): value.strip()
                for key, value in row.items()
                if key and value and value.strip()
            }

            if cleaned:  # skip empty rows
                cleaned['_row_index'] = i + 2  # for user feedback
                rows.append(cleaned)

    return rows

# Example usage
rows = read_csv_flexible(Path("messy_data.csv"))
# Returns: [
#   {'Student Name': 'Anna', 'Type': 'B', 'Topic': '...', '_row_index': 2},
#   {'Student Name': 'Tom', 'Type': 'Master', 'Topic': '...', '_row_index': 3},
#   ...
# ]
```

**Key points:**
- `csv.Sniffer()` auto-detects delimiters (comma, semicolon, tab)
- Return simple dictionaries - let AI figure out what columns mean
- Add `_row_index` for error messages ("Row 5 failed to parse")

---

## Using AI to Extract Structure

### Converting Chaos to Structure

```python
import json

async def parse_csv_row(agent: Agent, row_dict: dict) -> ThesisData:
    """Use AI to extract structured data from a raw CSV row"""

    # Convert dict to readable JSON for the AI
    row_json = json.dumps(row_dict, indent=2, ensure_ascii=False)

    prompt = f"""
    Extract thesis data from this CSV row:

    ```json
    {row_json}
    ```

    Extract all available information. Handle variations in column names.
    """

    result = await agent.run(prompt)
    return result.data  # Validated ThesisData object

# Example
row = {
    'Student Name': 'Müller Anna',
    'Type': 'B',
    'Topic': 'Efficient Graph Algorithms',
    'Advisor': 'Prof. Schmidt',
    'Registration': '15.3.2023',
    'Notes': 'Informatik Semester 6 - Note 1.3'
}

thesis_data = await parse_csv_row(parser_agent, row)
# Result:
#   student_first_name: "Anna"
#   student_last_name: "Müller"
#   thesis_type: "bachelor"
#   title: "Efficient Graph Algorithms"
#   supervisor_names: ["Prof. Schmidt"]
```

### Handling Dates Flexibly

Add to your Pydantic model:

```python
from pydantic import field_validator
from datetime import datetime

class ThesisData(BaseModel):
    date_registration: str | None = None  # Will be YYYY-MM-DD

    @field_validator('date_registration', mode='before')
    @classmethod
    def parse_flexible_date(cls, v):
        """AI should give us YYYY-MM-DD, but validate anyway"""
        if not v:
            return None

        # Try multiple formats
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                date = datetime.strptime(v, fmt)
                return date.strftime('%Y-%m-%d')
            except:
                continue

        # If all fail, ask AI to handle it
        return None  # or raise error
```

**Better approach:** Let the AI handle date conversion in the system prompt:

```python
system_prompt = """
...
Convert all dates to YYYY-MM-DD format.
Examples:
- "15.3.2023" → "2023-03-15"
- "20/04/2023" → "2023-04-20"
- "15-03-23" → "2023-03-15"
"""
```

---

## Fuzzy Matching Existing Records

### Why Fuzzy Matching?

Old data often has slight variations:
- "Anna Müller" vs "Anna Mueller" vs "Müller, Anna"
- "Prof. Dr. Schmidt" vs "Schmidt" vs "P. Schmidt"
- "anna.mueller@uni.de" vs "a.mueller@university.edu"

### Implementation

```python
from difflib import SequenceMatcher

def find_similar_students(
    first_name: str,
    last_name: str,
    email: str | None,
    existing_students: list[dict],
    threshold: float = 0.8
) -> list[tuple[dict, float]]:
    """
    Find similar students in the database.

    Returns: List of (student_dict, similarity_score) sorted by score
    """
    matches = []

    for student in existing_students:
        scores = []

        # Email match = highest priority (exact match)
        if email and student.get('email'):
            if email.lower() == student['email'].lower():
                return [(student, 1.0)]  # Perfect match!

        # Name similarity
        if first_name and student.get('first_name'):
            score = SequenceMatcher(
                None,
                first_name.lower(),
                student['first_name'].lower()
            ).ratio()
            scores.append(score)

        if last_name and student.get('last_name'):
            score = SequenceMatcher(
                None,
                last_name.lower(),
                student['last_name'].lower()
            ).ratio()
            scores.append(score)

        # Average score
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score >= threshold:
                matches.append((student, avg_score))

    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

# Usage
existing = [
    {'id': 1, 'first_name': 'Anna', 'last_name': 'Mueller', 'email': 'a.mueller@uni.de'},
    {'id': 2, 'first_name': 'Thomas', 'last_name': 'Schmidt', 'email': 't.schmidt@uni.de'},
]

matches = find_similar_students(
    first_name='Anna',
    last_name='Müller',  # Different spelling!
    email=None,
    existing_students=existing
)

# Result: [(student_1, 0.95)]  # High match despite ü vs ue
```

### Displaying Matches to User

```python
def show_matches(matches: list[tuple[dict, float]]):
    """Show similar matches for user to choose"""
    if not matches:
        print("No similar students found")
        return None

    print("\nSimilar students found:")
    for i, (student, score) in enumerate(matches[:5], 1):
        print(f"  {i}. {student['first_name']} {student['last_name']}")
        print(f"     Email: {student['email']}")
        print(f"     Match: {score:.0%}")

    print("  0. None of these - create new student")

    choice = input("\nChoose [0-5]: ").strip()
    if choice == '0':
        return None

    idx = int(choice) - 1
    if 0 <= idx < len(matches):
        return matches[idx][0]  # Return the student dict

    return None
```

---

## Interactive User Confirmation

### Pattern: Preview then Confirm

```python
async def import_row_interactive(row_dict: dict):
    """Import one row with user confirmation at each step"""

    # 1. Parse with AI
    print(f"\n{'='*60}")
    print(f"ROW {row_dict['_row_index']}")
    print(f"{'='*60}")

    thesis_data = await parse_csv_row(parser_agent, row_dict)

    # 2. Show what was extracted
    print("\n📋 Extracted:")
    print(f"  Student: {thesis_data.student_first_name} {thesis_data.student_last_name}")
    print(f"  Type: {thesis_data.thesis_type}")
    print(f"  Title: {thesis_data.title or '(none)'}")

    # 3. Find existing student
    print("\n🔍 Checking for existing student...")
    matches = find_similar_students(
        thesis_data.student_first_name,
        thesis_data.student_last_name,
        None,  # email if available
        existing_students
    )

    if matches and matches[0][1] > 0.95:
        student = matches[0][0]
        print(f"✅ Found exact match: {student['first_name']} {student['last_name']}")

        if not ask_yes_no("Use this student?"):
            student = None
    else:
        student = show_matches(matches)

    # 4. Create if needed
    if not student:
        if ask_yes_no(f"Create new student: {thesis_data.student_first_name} {thesis_data.student_last_name}?"):
            student = create_student_via_api(...)
            print(f"✅ Created student ID: {student['id']}")
        else:
            print("⏭️  Skipped")
            return False

    # 5. Continue with supervisors, thesis, etc...
    # ... similar pattern ...

    return True
```

**Key principles:**
1. Show what you're about to do
2. Ask before doing it
3. Provide clear options
4. Allow skipping/aborting

---

## Working with the API

### Basic API Client Pattern

```python
import requests
from typing import Optional

class ThesisManagerClient:
    """Simple API client for Thesis Manager"""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        })

    def list_students(self) -> list[dict]:
        """Get all students"""
        response = self.session.get(f"{self.url}/api/students/")
        response.raise_for_status()
        data = response.json()

        # Handle both list and paginated responses
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        return []

    def create_student(
        self,
        first_name: str,
        last_name: str,
        email: str,
        student_id: str | None = None
    ) -> dict:
        """Create a new student"""
        payload = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }
        if student_id:
            payload['student_id'] = student_id

        response = self.session.post(
            f"{self.url}/api/students/",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def create_thesis(
        self,
        thesis_type: str,
        student_ids: list[int],
        supervisor_ids: list[int],
        title: str | None = None,
        phase: str = 'first_contact',
        **kwargs  # dates, description, etc.
    ) -> dict:
        """Create a new thesis"""
        payload = {
            'thesis_type': thesis_type,
            'students': student_ids,
            'supervisors': supervisor_ids,
            'phase': phase
        }

        # Add optional fields
        if title:
            payload['title'] = title
        payload.update(kwargs)

        response = self.session.post(
            f"{self.url}/api/theses/",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ThesisManagerClient(
    url='http://localhost',
    token='your-api-token'
)

# Get all existing students (cache this!)
all_students = client.list_students()

# Create new student
student = client.create_student(
    first_name='Anna',
    last_name='Müller',
    email='anna.mueller@example.com'
)

# Create thesis
thesis = client.create_thesis(
    thesis_type='bachelor',
    student_ids=[student['id']],
    supervisor_ids=[supervisor['id']],
    title='My Thesis Topic',
    date_first_contact='2023-01-15'
)
```

### Caching for Performance

**Don't fetch students/supervisors for every row!**

```python
class ImportTool:
    """Helper with caching"""

    def __init__(self, client: ThesisManagerClient):
        self.client = client
        self._students_cache = None
        self._supervisors_cache = None

    def get_all_students(self) -> list[dict]:
        """Get all students (cached)"""
        if self._students_cache is None:
            print("📥 Loading all students from API...")
            self._students_cache = self.client.list_students()
            print(f"   Loaded {len(self._students_cache)} students")
        return self._students_cache

    def create_student(self, **kwargs) -> dict:
        """Create and update cache"""
        student = self.client.create_student(**kwargs)
        if self._students_cache is not None:
            self._students_cache.append(student)
        return student
```

---

## Putting It All Together

### Main Script Structure

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path

async def main():
    # 1. Setup
    csv_path = Path("my_messy_data.csv")

    client = ThesisManagerClient(url='...', token='...')
    tool = ImportTool(client)

    # Create AI agent
    agent = Agent(...)

    # 2. Read CSV
    rows = read_csv_flexible(csv_path)
    print(f"📄 Read {len(rows)} rows from CSV\n")

    # 3. Load existing data once
    all_students = tool.get_all_students()
    all_supervisors = tool.get_all_supervisors()
    print(f"📚 Database has {len(all_students)} students, {len(all_supervisors)} supervisors\n")

    # 4. Process each row
    success = 0
    skipped = 0

    for row in rows:
        try:
            if await import_row_interactive(agent, tool, row):
                success += 1
            else:
                skipped += 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            skipped += 1

    # 5. Summary
    print(f"\n{'='*60}")
    print("IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Imported: {success}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"{'='*60}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Running It

```bash
# Set environment variables
export THESIS_MANAGER_URL=http://localhost
export THESIS_MANAGER_API_TOKEN=your-token
export ANTHROPIC_API_KEY=your-key

# Run import
python import_script.py
```

---

## Tips and Best Practices

### 1. Start with Dry Run

Add a `--dry-run` flag that parses and shows what would be created, but doesn't actually call the API.

```python
if args.dry_run:
    print("🔍 DRY RUN - No changes will be made")
    # Parse and show, but don't create
```

### 2. Handle Errors Gracefully

```python
try:
    student = client.create_student(...)
except requests.HTTPError as e:
    if e.response.status_code == 400:
        # Validation error - show details
        print(f"❌ Validation error: {e.response.json()}")
    elif e.response.status_code == 409:
        # Conflict - maybe email already exists
        print("❌ Student with this email already exists")
    else:
        raise
```

### 3. Resume Support

Add a `--start-from` option:

```python
parser.add_argument('--start-from', type=int, default=1)

# Filter rows
rows = [r for r in rows if r['_row_index'] >= args.start_from]
```

### 4. Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('import.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting import...")
```

### 5. Progress Feedback

```python
for i, row in enumerate(rows, 1):
    print(f"\n[{i}/{len(rows)}] Processing row {row['_row_index']}...")
```

---

## Example: Complete Minimal Importer

Here's a ~100 line minimal working example:

```python
#!/usr/bin/env python3
import asyncio
import csv
import json
from pathlib import Path
from pydantic_ai import Agent
from pydantic import BaseModel

class ThesisData(BaseModel):
    student_first_name: str
    student_last_name: str
    thesis_type: str
    title: str | None = None

# Setup
agent = Agent(
    model='anthropic:claude-3-5-sonnet-20241022',
    result_type=ThesisData,
    system_prompt="Extract thesis data from CSV. Handle any column names."
)

def read_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))

async def parse_row(row: dict) -> ThesisData:
    prompt = f"Extract data from: {json.dumps(row)}"
    result = await agent.run(prompt)
    return result.data

async def main():
    rows = read_csv(Path("data.csv"))

    for row in rows:
        data = await parse_row(row)
        print(f"Student: {data.student_first_name} {data.student_last_name}")
        print(f"Type: {data.thesis_type}")
        print(f"Title: {data.title}")
        print()

asyncio.run(main())
```

Run it and see the AI extract structured data from your messy CSV!

---

## Next Steps

1. **Start simple:** Just parse and print what the AI extracts
2. **Add fuzzy matching:** Find existing students before creating
3. **Add interactivity:** Ask user to confirm matches
4. **Add API calls:** Actually create records
5. **Add resume support:** Handle interruptions gracefully

You now have all the building blocks. Good luck! 🚀

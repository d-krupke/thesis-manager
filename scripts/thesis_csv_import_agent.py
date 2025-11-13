"""
PydanticAI Agent for importing thesis data from CSV files.

This agent intelligently parses ARBITRARY CSV formats - it doesn't require specific
column names or structure. It uses AI to understand chaotic, real-world thesis data.
"""

import csv
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from pydantic_ai import Agent
from pydantic import BaseModel, Field

from utils.thesis_manager_client import ThesisManagerClient
from utils.csv_import_tool import CSVImportTool
from utils.csv_import_models import ThesisInfo

logger = logging.getLogger(__name__)


class ParsedCSVRow(BaseModel):
    """Result of parsing a single CSV row."""
    success: bool = Field(description="Whether parsing was successful")
    thesis_info: Optional[ThesisInfo] = Field(None, description="Extracted thesis information")
    error_message: Optional[str] = Field(None, description="Error message if parsing failed")


class ThesisCSVImportAgent:
    """
    Agent for importing thesis data from CSV files using PydanticAI.

    This agent can handle chaotic CSV files with varying column names, missing data,
    and non-uniform formats - exactly what you get from handcrafted spreadsheets.
    """

    def __init__(self, client: ThesisManagerClient, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the import agent.

        Args:
            client: ThesisManagerClient for API access
            model: Model to use for PydanticAI agent
        """
        self.client = client
        self.tool = CSVImportTool(client)
        self.model = model

        # Create the parsing agent
        self.parser_agent = Agent(
            model=f'anthropic:{model}',
            result_type=ParsedCSVRow,
            system_prompt=self._get_parser_system_prompt()
        )

    def _get_parser_system_prompt(self) -> str:
        """Get the system prompt for the CSV parser agent."""
        return """You are an expert at extracting thesis data from messy, handcrafted CSV/spreadsheet rows.

Your task is to extract ONLY the information that goes into the Thesis Manager system:

**REQUIRED TO EXTRACT:**
1. Student: first name, last name (required), email (if available), student ID/Matr.Nr. (if available)
2. Thesis Type: bachelor, master, project, or other (look for B/M/P, "Bachelor", "Master", etc.)

**OPTIONAL TO EXTRACT:**
3. Supervisors: Extract names of supervisors/advisors/reviewers from any text fields
   - Look for titles like "Prof.", "Dr.", "Prof. Dr."
   - Names may be in fields like "Betreuer", "Aufgabenstellung", "Zweitgutachter", etc.
   - Extract multiple supervisors if present
   - Try to identify email addresses if mentioned

4. Thesis details:
   - Title/topic/theme
   - Phase: Infer from available data (completed if grade exists, submitted if submission date exists, abandoned if no recent activity, etc.)

5. Dates (convert to YYYY-MM-DD format):
   - First contact (Erstkontakt)
   - Registration (Anmeldung)
   - Deadline (Abgabe, Abgabedatum)
   - Presentation (Vortrag, Kolloquium)

6. Additional notes: Any other relevant info (degree program, grade, semester) goes into description field

**IMPORTANT:**
- Column names vary wildly - use context and content to understand meaning
- Handle German terms, abbreviations, misspellings
- Parse dates flexibly (DD.MM.YYYY, YYYY-MM-DD, D.M.YY, etc.)
- Missing data is OK - extract what you can
- If student name is missing => mark as error
- If thesis type is unclear => use 'other'
- Add warnings for data quality issues

**OUTPUT:**
Return ThesisInfo with all extracted data. Be flexible and pragmatic - this is migration from messy real-world data."""

    async def parse_csv_row(self, row_index: int, row_dict: Dict[str, Any]) -> ParsedCSVRow:
        """
        Parse a single CSV row using the PydanticAI agent.

        Args:
            row_index: Row number (for user feedback)
            row_dict: Raw CSV row as dictionary (column_name -> value)

        Returns:
            Parsed thesis information
        """
        # Format the row data as JSON for the agent
        row_json = json.dumps(row_dict, indent=2, ensure_ascii=False)

        prompt = f"""Extract thesis data from CSV row {row_index}:

```json
{row_json}
```

Extract all available thesis information. This is real-world migration data - be flexible with column names and formats."""

        try:
            result = await self.parser_agent.run(prompt)
            return result.data
        except Exception as e:
            logger.error("Error parsing row %d: %s", row_index, e)
            logger.debug("Row data was: %s", row_dict)
            return ParsedCSVRow(
                success=False,
                error_message=f"Failed to parse: {str(e)}"
            )

    def read_csv_file(self, csv_file: Path) -> List[Dict[str, Any]]:
        """
        Read a CSV file and return raw rows as dictionaries.

        Args:
            csv_file: Path to CSV file

        Returns:
            List of dictionaries (one per CSV row)
        """
        rows = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(2048)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
            except:
                # Fall back to comma
                dialect = csv.excel()

            reader = csv.DictReader(f, dialect=dialect)

            for i, row in enumerate(reader):
                # Clean up the row: remove empty values and strip whitespace
                cleaned_row = {}
                for key, value in row.items():
                    if key is None:  # Handle unnamed columns
                        continue
                    if value is None or str(value).strip() == '':
                        continue
                    cleaned_row[key.strip()] = str(value).strip()

                # Skip completely empty rows
                if not cleaned_row:
                    logger.debug("Skipping empty row %d", i + 2)
                    continue

                # Add row index for tracking
                cleaned_row['_row_index'] = i + 2  # +2 for header and 0-indexing

                rows.append(cleaned_row)

        logger.info("Read %d non-empty rows from CSV", len(rows))
        return rows

    async def process_row(
        self,
        row_dict: Dict[str, Any],
        dry_run: bool = False
    ) -> bool:
        """
        Process a single CSV row: parse, match, and show summary.

        Args:
            row_dict: Raw CSV row dictionary
            dry_run: If True, only analyze without making changes

        Returns:
            True if processed successfully, False otherwise
        """
        row_index = row_dict.get('_row_index', '?')

        logger.info("\n" + "="*80)
        logger.info("Processing row %s", row_index)
        logger.info("="*80)

        # Parse the row using the agent
        parsed = await self.parse_csv_row(row_index, row_dict)

        if not parsed.success or not parsed.thesis_info:
            logger.error("Failed to parse row %s: %s", row_index, parsed.error_message)
            return False

        thesis_info = parsed.thesis_info

        # Find or create student
        student_match, student_suggestions = self.tool.find_or_suggest_student(thesis_info.student)

        # Find or create supervisors
        supervisor_matches = []
        supervisor_suggestions = []
        for sup_info in thesis_info.supervisors:
            match, suggestions = self.tool.find_or_suggest_supervisor(sup_info)
            supervisor_matches.append(match)
            supervisor_suggestions.append(suggestions)

        # Check for similar theses
        potential_student_ids = []
        if student_match:
            potential_student_ids = [student_match['id']]
        elif student_suggestions:
            # Use first suggestion for thesis matching
            potential_student_ids = [student_suggestions[0][0]['id']]

        thesis_matches = []
        if potential_student_ids:
            thesis_matches = self.tool.find_similar_theses(
                thesis_info,
                potential_student_ids,
                threshold=0.7
            )

        # Format and display summary
        summary = self.tool.format_import_summary(
            thesis_info,
            student_match,
            student_suggestions,
            supervisor_matches,
            supervisor_suggestions,
            thesis_matches
        )

        print(summary)

        if dry_run:
            logger.info("DRY RUN - not making any changes")
            return True

        # This is where interactive confirmation would happen in the CLI
        # For now, we'll return True to indicate parsing was successful
        return True


def main():
    """
    Main entry point (for testing only).

    The actual CLI will be implemented separately.
    """
    import asyncio
    import os

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # This is just for testing the agent structure
    print("ThesisCSVImportAgent initialized")
    print("Use the CLI script to actually import data")


if __name__ == '__main__':
    main()

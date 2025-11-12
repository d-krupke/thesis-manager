"""
PydanticAI Agent for importing thesis data from CSV files.

This agent uses PydanticAI to intelligently parse CSV data and import it
into the Thesis Manager system with user confirmation at each step.
"""

import csv
import logging
from typing import Optional, List
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field

from utils.thesis_manager_client import ThesisManagerClient
from utils.csv_import_tool import CSVImportTool
from utils.csv_import_models import CSVRowData, ThesisInfo, StudentInfo, SupervisorInfo

logger = logging.getLogger(__name__)


class ParsedCSVRow(BaseModel):
    """Result of parsing a single CSV row."""
    success: bool = Field(description="Whether parsing was successful")
    thesis_info: Optional[ThesisInfo] = Field(None, description="Extracted thesis information")
    error_message: Optional[str] = Field(None, description="Error message if parsing failed")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")


class ThesisCSVImportAgent:
    """
    Agent for importing thesis data from CSV files using PydanticAI.
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
        return """You are an expert at parsing thesis data from German CSV files.

Your task is to extract structured thesis information from CSV rows that contain:
- Student information (Name, Vorname, Email, Matr. Nr.)
- Supervisor information (may be in free text fields like "Aufgabenst. u. Betreuer", "Betreuer WMA", "Zweitgutachter")
- Thesis details (B/M/P for type, Thema for title, various dates)
- Additional metadata (Studiengang, Semesterzahl, grades, etc.)

Guidelines:
1. Extract all available information, even if incomplete
2. Parse dates in various formats (DD.MM.YYYY, YYYY-MM-DD, etc.) to YYYY-MM-DD
3. Identify supervisors from text fields - they may contain names, roles, or be empty
4. Map B/M/P to bachelor/master/project thesis types
5. Infer the current phase from available dates:
   - If "abgegeben am" (submitted) is filled: phase is 'submitted' or later
   - If "Vortrag am" (presentation) is filled: phase is 'defended' or later
   - If "Note" (grade) is filled: phase is 'completed'
   - If only early dates: phase is 'first_contact', 'registered', or 'working'
   - If data looks abandoned (no activity): phase is 'abandoned'
6. Handle missing or malformed data gracefully - mark fields as missing
7. Generate warnings for data quality issues

Be thorough and extract as much as possible to help migrate legacy data."""

    async def parse_csv_row(self, row_data: CSVRowData) -> ParsedCSVRow:
        """
        Parse a single CSV row using the PydanticAI agent.

        Args:
            row_data: CSV row data

        Returns:
            Parsed thesis information
        """
        # Build a prompt from the row data
        prompt = f"""Parse the following thesis data from CSV row {row_data.row_index}:

Student:
- Name (last name): {row_data.name or 'MISSING'}
- Vorname (first name): {row_data.vorname or 'MISSING'}
- Email: {row_data.email or 'MISSING'}
- Matr. Nr.: {row_data.matr_nr or 'MISSING'}

Thesis:
- Type (B/M/P): {row_data.thesis_type or 'MISSING'}
- Thema (topic): {row_data.thema or 'MISSING'}

Dates:
- Erstkontakt (first contact): {row_data.erstkontakt or 'MISSING'}
- Anmeldung Datum (registration): {row_data.anmeldung_datum or 'MISSING'}
- Abgabe Datum (deadline): {row_data.abgabe_datum or 'MISSING'}
- abgegeben am (submitted): {row_data.abgegeben_am or 'MISSING'}
- Vortrag am (presentation): {row_data.vortrag_am or 'MISSING'}

Supervisors/Reviewers:
- Aufgabenst. u. Betreuer: {row_data.aufgabenstellung_betreuer or 'MISSING'}
- Betreuer WMA: {row_data.betreuer_wma or 'MISSING'}
- Zweitgutachter (second reviewer): {row_data.zweitgutachter or 'MISSING'}

Additional:
- Studiengang (degree program): {row_data.studiengang or 'MISSING'}
- Semesterzahl: {row_data.semesterzahl or 'MISSING'}
- Note (grade): {row_data.note or 'MISSING'}
- Noten: {row_data.noten or 'MISSING'}
- Literatur-Recherche: {row_data.literatur_recherche or 'MISSING'}
- Beschreibung: {row_data.beschreibung or 'MISSING'}

Extract all available information into the structured format."""

        try:
            result = await self.parser_agent.run(prompt)
            return result.data
        except Exception as e:
            logger.error("Error parsing row %d: %s", row_data.row_index, e)
            return ParsedCSVRow(
                success=False,
                error_message=f"Failed to parse: {str(e)}"
            )

    def read_csv_file(self, csv_file: Path) -> List[CSVRowData]:
        """
        Read a CSV file and convert to CSVRowData objects.

        Args:
            csv_file: Path to CSV file

        Returns:
            List of CSVRowData objects
        """
        rows = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try to detect dialect
            sample = f.read(1024)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)

            reader = csv.DictReader(f, dialect=dialect)

            for i, row in enumerate(reader):
                # Map CSV columns to CSVRowData fields
                row_data = CSVRowData(
                    row_index=i + 2,  # +2 because of 0-index and header row
                    name=row.get('Name'),
                    vorname=row.get('Vorname'),
                    email=row.get('Email-Adresse'),
                    anmeldung_datum=row.get('Anmeldung Datum'),
                    abgabe_datum=row.get('Abgabe  Datum') or row.get('Abgabe Datum'),  # Handle extra space
                    studiengang=row.get('Studiengang'),
                    semesterzahl=row.get('Semesterzahl'),
                    alg_veranstaltungen=row.get('ALG-Veranstaltungen'),
                    thesis_type=row.get('B/M/P'),
                    matr_nr=row.get('Matr. Nr.'),
                    erstkontakt=row.get('Erstkontakt'),
                    aufgabenstellung_betreuer=row.get('Aufgabenst. u. Betreuer'),
                    thema=row.get('Thema'),
                    noten=row.get('Noten'),
                    literatur_recherche=row.get('Literatur- Recherche') or row.get('Literatur-Recherche'),
                    abgegeben_am=row.get('abgegeben am'),
                    vortrag_am=row.get('Vortrag am'),
                    betreuer_wma=row.get('Betreuer WMA'),
                    zweitgutachter=row.get('Zweitgutachter'),
                    note=row.get('Note'),
                    beschreibung=row.get('Besch. 4,0 + Vortr.')
                )

                # Skip completely empty rows
                if not any([
                    row_data.name, row_data.vorname, row_data.thesis_type,
                    row_data.thema, row_data.email
                ]):
                    logger.debug("Skipping empty row %d", row_data.row_index)
                    continue

                rows.append(row_data)

        logger.info("Read %d non-empty rows from CSV", len(rows))
        return rows

    async def process_row(
        self,
        row_data: CSVRowData,
        dry_run: bool = False
    ) -> bool:
        """
        Process a single CSV row: parse, match, and import.

        Args:
            row_data: CSV row data
            dry_run: If True, only analyze without making changes

        Returns:
            True if processed successfully, False otherwise
        """
        logger.info("\n" + "="*80)
        logger.info("Processing row %d: %s", row_data.row_index, row_data)
        logger.info("="*80)

        # Parse the row using the agent
        parsed = await self.parse_csv_row(row_data)

        if not parsed.success or not parsed.thesis_info:
            logger.error("Failed to parse row %d: %s", row_data.row_index, parsed.error_message)
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

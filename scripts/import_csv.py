#!/usr/bin/env python3
"""
Interactive CLI for importing thesis data from CSV files.

This script uses a PydanticAI agent to parse CSV data and provides
interactive confirmation at each step before making changes to the database.
"""

import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

from utils.thesis_manager_client import ThesisManagerClient
from utils.csv_import_tool import CSVImportTool
from thesis_csv_import_agent import ThesisCSVImportAgent
from utils.csv_import_models import ThesisInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no answer.

    Args:
        question: Question to ask
        default: Default answer if user just presses Enter

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{question} [{default_str}]: ").strip().lower()

        if not response:
            return default

        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please answer 'y' or 'n'")


def prompt_choice(question: str, choices: List[str], allow_none: bool = True) -> Optional[int]:
    """
    Prompt user to choose from a list.

    Args:
        question: Question to ask
        choices: List of choice strings
        allow_none: Whether to allow "skip" option

    Returns:
        Index of chosen option (0-based) or None if skipped
    """
    print(f"\n{question}")
    for i, choice in enumerate(choices):
        print(f"  {i+1}. {choice}")

    if allow_none:
        print(f"  0. Skip / Create new")

    while True:
        try:
            response = input(f"Choose [1-{len(choices)}" + (" or 0]: " if allow_none else "]: ")).strip()

            if not response:
                continue

            choice_num = int(response)

            if allow_none and choice_num == 0:
                return None

            if 1 <= choice_num <= len(choices):
                return choice_num - 1

            print(f"Please choose a number between {'0 and' if allow_none else '1 and'} {len(choices)}")

        except ValueError:
            print("Please enter a number")


async def import_single_row(
    agent: ThesisCSVImportAgent,
    tool: CSVImportTool,
    row_dict: Dict[str, Any],
    interactive: bool = True
) -> bool:
    """
    Import a single CSV row with user confirmation.

    Args:
        agent: Import agent
        tool: Import tool
        row_dict: Raw CSV row dictionary
        interactive: Whether to ask for user confirmation

    Returns:
        True if imported successfully, False otherwise
    """
    row_index = row_dict.get('_row_index', '?')

    print("\n" + "=" * 80)
    print(f"ROW {row_index}")
    print("=" * 80)

    # Show raw CSV data
    print("\n📄 CSV Data:")
    for key, value in row_dict.items():
        if key == '_row_index':
            continue
        print(f"  {key}: {value}")

    # Parse the row
    parsed = await agent.parse_csv_row(row_index, row_dict)

    if not parsed.success or not parsed.thesis_info:
        print(f"❌ ERROR: {parsed.error_message}")
        return False

    thesis_info = parsed.thesis_info

    # Display parsed information
    print("\n📋 PARSED DATA:")
    print(f"  Student: {thesis_info.student}")
    print(f"  Type: {thesis_info.thesis_type}")
    print(f"  Title: {thesis_info.title or '(none)'}")
    print(f"  Phase: {thesis_info.phase}")
    if thesis_info.supervisors:
        print(f"  Supervisors: {len(thesis_info.supervisors)}")
        for i, sup in enumerate(thesis_info.supervisors, 1):
            print(f"    {i}. {sup}")

    if parsed.warnings:
        print("\n⚠️  WARNINGS:")
        for warning in parsed.warnings:
            print(f"  - {warning}")

    if thesis_info.missing_fields:
        print(f"\nℹ️  Missing fields: {', '.join(thesis_info.missing_fields)}")

    # Step 1: Handle Student
    print("\n" + "-" * 80)
    print("STEP 1: STUDENT")
    print("-" * 80)

    student_match, student_suggestions = tool.find_or_suggest_student(thesis_info.student)
    student_id = None

    if student_match:
        print(f"✅ Found exact match: {student_match['first_name']} {student_match['last_name']} (ID: {student_match['id']})")
        if interactive and not prompt_yes_no("Use this student?", default=True):
            student_match = None

    if not student_match and student_suggestions:
        print("\n🔍 Similar students found:")
        for match, score in student_suggestions[:5]:
            print(f"  {match['first_name']} {match['last_name']} ({match['email']}) - {score:.0%} match")

        if interactive:
            choices = [
                f"{m['first_name']} {m['last_name']} ({m['email']})"
                for m, _ in student_suggestions[:5]
            ]
            choice_idx = prompt_choice("Which student to use?", choices, allow_none=True)

            if choice_idx is not None:
                student_match = student_suggestions[choice_idx][0]

    if student_match:
        student_id = student_match['id']
        print(f"✅ Using student ID: {student_id}")
    else:
        if not interactive or prompt_yes_no(f"Create new student: {thesis_info.student}?", default=True):
            print("Creating new student...")
            created = tool.create_student(thesis_info.student)
            if created:
                student_id = created['id']
                print(f"✅ Created student ID: {student_id}")
            else:
                print("❌ Failed to create student")
                return False
        else:
            print("⏭️  Skipped - student not created")
            return False

    # Step 2: Handle Supervisors
    print("\n" + "-" * 80)
    print("STEP 2: SUPERVISORS")
    print("-" * 80)

    supervisor_ids = []

    if not thesis_info.supervisors:
        print("ℹ️  No supervisors specified in CSV")
    else:
        for i, sup_info in enumerate(thesis_info.supervisors, 1):
            print(f"\nSupervisor {i}/{len(thesis_info.supervisors)}: {sup_info}")

            sup_match, sup_suggestions = tool.find_or_suggest_supervisor(sup_info)
            sup_id = None

            if sup_match:
                print(f"✅ Found exact match: {sup_match['first_name']} {sup_match['last_name']} (ID: {sup_match['id']})")
                if interactive and not prompt_yes_no("Use this supervisor?", default=True):
                    sup_match = None

            if not sup_match and sup_suggestions:
                print("\n🔍 Similar supervisors found:")
                for match, score in sup_suggestions[:5]:
                    print(f"  {match['first_name']} {match['last_name']} ({match['email']}) - {score:.0%} match")

                if interactive:
                    choices = [
                        f"{m['first_name']} {m['last_name']} ({m['email']})"
                        for m, _ in sup_suggestions[:5]
                    ]
                    choice_idx = prompt_choice("Which supervisor to use?", choices, allow_none=True)

                    if choice_idx is not None:
                        sup_match = sup_suggestions[choice_idx][0]

            if sup_match:
                sup_id = sup_match['id']
                print(f"✅ Using supervisor ID: {sup_id}")
            else:
                if not interactive or prompt_yes_no(f"Create new supervisor: {sup_info}?", default=True):
                    print("Creating new supervisor...")
                    created = tool.create_supervisor(sup_info)
                    if created:
                        sup_id = created['id']
                        print(f"✅ Created supervisor ID: {sup_id}")
                    else:
                        print("⚠️  Failed to create supervisor - continuing without")

            if sup_id:
                supervisor_ids.append(sup_id)

    if not supervisor_ids:
        print("\n⚠️  WARNING: No supervisors assigned to this thesis")
        if interactive and not prompt_yes_no("Continue without supervisors?", default=True):
            return False

    # Step 3: Check for duplicate theses
    print("\n" + "-" * 80)
    print("STEP 3: CHECK FOR DUPLICATES")
    print("-" * 80)

    thesis_matches = tool.find_similar_theses(
        thesis_info,
        [student_id],
        threshold=0.6
    )

    if thesis_matches:
        print("\n⚠️  WARNING: Similar theses found!")
        for thesis, score, reason in thesis_matches[:3]:
            print(f"  [{thesis.get('thesis_type')}] {thesis.get('title', 'Untitled')}")
            print(f"    Phase: {thesis.get('phase')}, Match: {score:.0%} ({reason})")

        if interactive and not prompt_yes_no("This might be a duplicate. Continue anyway?", default=False):
            print("⏭️  Skipped - possible duplicate")
            return False
    else:
        print("✅ No similar theses found")

    # Step 4: Create thesis
    print("\n" + "-" * 80)
    print("STEP 4: CREATE THESIS")
    print("-" * 80)

    print(f"\n📝 Ready to create:")
    print(f"  Type: {thesis_info.thesis_type}")
    print(f"  Title: {thesis_info.title or 'Untitled'}")
    print(f"  Student ID: {student_id}")
    print(f"  Supervisor IDs: {supervisor_ids if supervisor_ids else '(none)'}")
    print(f"  Phase: {thesis_info.phase}")

    if not interactive or prompt_yes_no("Create this thesis?", default=True):
        print("Creating thesis...")
        created = tool.create_thesis(thesis_info, [student_id], supervisor_ids)
        if created:
            thesis_id = created['id']
            print(f"✅ Created thesis ID: {thesis_id}")
            return True
        else:
            print("❌ Failed to create thesis")
            return False
    else:
        print("⏭️  Skipped - thesis not created")
        return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import thesis data from CSV file into Thesis Manager"
    )
    parser.add_argument(
        'csv_file',
        type=Path,
        help='Path to CSV file to import'
    )
    parser.add_argument(
        '--url',
        help='Thesis Manager URL (or set THESIS_MANAGER_URL env var)',
        default=None
    )
    parser.add_argument(
        '--token',
        help='API token (or set THESIS_MANAGER_API_TOKEN env var)',
        default=None
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run without user confirmation (use defaults)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and analyze CSV without making any changes'
    )
    parser.add_argument(
        '--start-from',
        type=int,
        default=1,
        help='Start from specific row number (default: 1)'
    )
    parser.add_argument(
        '--model',
        default='claude-3-5-sonnet-20241022',
        help='Model to use for parsing (default: claude-3-5-sonnet-20241022)'
    )

    args = parser.parse_args()

    # Check if CSV file exists
    if not args.csv_file.exists():
        print(f"❌ ERROR: File not found: {args.csv_file}")
        sys.exit(1)

    print("=" * 80)
    print("THESIS MANAGER CSV IMPORT TOOL")
    print("=" * 80)
    print(f"CSV File: {args.csv_file}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'INTERACTIVE' if not args.non_interactive else 'AUTOMATIC'}")
    print(f"Model: {args.model}")
    print("=" * 80)

    # Initialize client
    try:
        client = ThesisManagerClient(url=args.url, token=args.token)
        print("✅ Connected to Thesis Manager API")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to API: {e}")
        sys.exit(1)

    # Initialize agent
    try:
        agent = ThesisCSVImportAgent(client, model=args.model)
        tool = agent.tool
        print("✅ Initialized import agent")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize agent: {e}")
        sys.exit(1)

    # Read CSV
    try:
        rows = agent.read_csv_file(args.csv_file)
        print(f"✅ Read {len(rows)} rows from CSV")
    except Exception as e:
        print(f"❌ ERROR: Failed to read CSV: {e}")
        sys.exit(1)

    if not rows:
        print("❌ No data rows found in CSV")
        sys.exit(1)

    # Filter rows if starting from a specific row
    if args.start_from > 1:
        rows = [r for r in rows if r.get('_row_index', 0) >= args.start_from]
        print(f"Starting from row {args.start_from} ({len(rows)} rows remaining)")

    # Process rows
    print("\n" + "=" * 80)
    print(f"PROCESSING {len(rows)} ROWS")
    print("=" * 80)

    success_count = 0
    skipped_count = 0
    error_count = 0

    for row in rows:
        try:
            if args.dry_run:
                # Just parse and display
                success = await agent.process_row(row, dry_run=True)
            else:
                # Actually import
                success = await import_single_row(
                    agent,
                    tool,
                    row,
                    interactive=not args.non_interactive
                )

            if success:
                success_count += 1
            else:
                skipped_count += 1

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ ERROR processing row {row.row_index}: {e}")
            logger.exception(e)
            error_count += 1

            if not args.non_interactive:
                if not prompt_yes_no("Continue with next row?", default=True):
                    break

    # Summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {success_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"Total processed: {success_count + skipped_count + error_count} / {len(rows)}")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())

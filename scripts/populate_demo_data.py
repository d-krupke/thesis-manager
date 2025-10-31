#!/usr/bin/env python3
"""
Demo Data Population Script for Thesis Manager

This script populates the Thesis Manager with example data for demonstration purposes.
It creates students, supervisors, theses in various phases, and sample comments using
the REST API.

Environment variables (from .env):
  THESIS_MANAGER_URL        - Thesis Manager instance URL (default: http://localhost)
  THESIS_MANAGER_API_TOKEN  - Knox authentication token (required)

Usage:
  # Set up your environment variables first
  export THESIS_MANAGER_URL="http://localhost"
  export THESIS_MANAGER_API_TOKEN="your_token_here"

  # Run the script
  python populate_demo_data.py

  # Or run with confirmation prompt disabled
  python populate_demo_data.py --yes

Features:
  - Creates 10 sample students
  - Creates 5 sample supervisors
  - Creates 15 theses in various phases (from first_contact to completed)
  - Adds sample comments to theses
  - Uses realistic academic data
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests

# Try to load dotenv if available
try:
    import dotenv
    dotenv.load_dotenv(dotenv.find_dotenv())
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ThesisManagerDemoClient:
    """Client for populating demo data via Thesis Manager API."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize demo data client.

        Args:
            url: Thesis Manager URL (defaults to THESIS_MANAGER_URL env var)
            token: Knox API token (defaults to THESIS_MANAGER_API_TOKEN env var)
        """
        self.url = (url or os.environ.get("THESIS_MANAGER_URL", "http://localhost")).rstrip('/')
        self.token = token or os.environ.get("THESIS_MANAGER_API_TOKEN")

        if not self.token:
            raise ValueError(
                "THESIS_MANAGER_API_TOKEN not set in environment.\n"
                "Please create an API token at: {}/api_tokens/".format(self.url)
            )

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
        })
        logger.info("Initialized Thesis Manager client for %s", self.url)

    def create_student(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a student via API."""
        url = f"{self.url}/api/students/"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            student = response.json()
            logger.info("Created student: %s %s", student.get('first_name'), student.get('last_name'))
            return student
        except requests.exceptions.RequestException as e:
            logger.error("Error creating student: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response: %s", e.response.text)
            return None

    def create_supervisor(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a supervisor via API."""
        url = f"{self.url}/api/supervisors/"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            supervisor = response.json()
            logger.info("Created supervisor: %s %s", supervisor.get('first_name'), supervisor.get('last_name'))
            return supervisor
        except requests.exceptions.RequestException as e:
            logger.error("Error creating supervisor: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response: %s", e.response.text)
            return None

    def create_thesis(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a thesis via API."""
        url = f"{self.url}/api/theses/"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            thesis = response.json()
            logger.info("Created thesis: %s (Phase: %s)", thesis.get('title'), thesis.get('phase'))
            return thesis
        except requests.exceptions.RequestException as e:
            logger.error("Error creating thesis: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response: %s", e.response.text)
            return None

    def add_comment(self, thesis_id: int, text: str, is_auto_generated: bool = False) -> Optional[Dict[str, Any]]:
        """Add a comment to a thesis."""
        url = f"{self.url}/api/theses/{thesis_id}/add_comment/"
        payload = {
            'text': text,
            'is_auto_generated': is_auto_generated,
        }
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            comment = response.json()
            logger.info("Added comment to thesis #%d", thesis_id)
            return comment
        except requests.exceptions.RequestException as e:
            logger.error("Error adding comment: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Response: %s", e.response.text)
            return None


# Demo data definitions
DEMO_STUDENTS = [
    {
        "first_name": "Emma",
        "last_name": "Johnson",
        "email": "emma.johnson@university.edu",
        "student_id": "STU001",
        "comments": "Excellent student, very motivated"
    },
    {
        "first_name": "Liam",
        "last_name": "Smith",
        "email": "liam.smith@university.edu",
        "student_id": "STU002",
        "comments": "Strong background in algorithms"
    },
    {
        "first_name": "Olivia",
        "last_name": "Brown",
        "email": "olivia.brown@university.edu",
        "student_id": "STU003",
        "comments": "Interested in machine learning"
    },
    {
        "first_name": "Noah",
        "last_name": "Davis",
        "email": "noah.davis@university.edu",
        "student_id": "STU004",
        "comments": "Working part-time, needs flexible schedule"
    },
    {
        "first_name": "Ava",
        "last_name": "Miller",
        "email": "ava.miller@university.edu",
        "student_id": "STU005",
        "comments": "Strong programming skills"
    },
    {
        "first_name": "Ethan",
        "last_name": "Wilson",
        "email": "ethan.wilson@university.edu",
        "student_id": "STU006",
        "comments": "Interested in web development"
    },
    {
        "first_name": "Sophia",
        "last_name": "Moore",
        "email": "sophia.moore@university.edu",
        "student_id": "STU007",
        "comments": "Background in data science"
    },
    {
        "first_name": "Mason",
        "last_name": "Taylor",
        "email": "mason.taylor@university.edu",
        "student_id": "STU008",
        "comments": "Good team player"
    },
    {
        "first_name": "Isabella",
        "last_name": "Anderson",
        "email": "isabella.anderson@university.edu",
        "student_id": "STU009",
        "comments": "Experience with mobile development"
    },
    {
        "first_name": "James",
        "last_name": "Thomas",
        "email": "james.thomas@university.edu",
        "student_id": "STU010",
        "comments": "Research-oriented, interested in PhD"
    },
]

DEMO_SUPERVISORS = [
    {
        "first_name": "Dr. Sarah",
        "last_name": "Chen",
        "email": "sarah.chen@university.edu",
        "comments": "Specialization: Machine Learning and AI"
    },
    {
        "first_name": "Prof. Michael",
        "last_name": "Rodriguez",
        "email": "michael.rodriguez@university.edu",
        "comments": "Specialization: Software Engineering"
    },
    {
        "first_name": "Dr. Lisa",
        "last_name": "Patel",
        "email": "lisa.patel@university.edu",
        "comments": "Specialization: Data Science and Visualization"
    },
    {
        "first_name": "Dr. David",
        "last_name": "Kim",
        "email": "david.kim@university.edu",
        "comments": "Specialization: Distributed Systems"
    },
    {
        "first_name": "Prof. Anna",
        "last_name": "Wagner",
        "email": "anna.wagner@university.edu",
        "comments": "Specialization: Human-Computer Interaction"
    },
]

def generate_demo_theses(student_ids: List[int], supervisor_ids: List[int]) -> List[Dict[str, Any]]:
    """Generate demo thesis data with various phases and dates."""
    today = datetime.now().date()

    theses = [
        # First Contact - Recent inquiries
        {
            "title": "Exploring Deep Learning Approaches for Medical Image Segmentation",
            "thesis_type": "master",
            "phase": "first_contact",
            "students": [student_ids[0]],
            "supervisors": [supervisor_ids[0]],
            "date_first_contact": (today - timedelta(days=5)).isoformat(),
            "description": "Initial inquiry about working with medical imaging datasets",
        },
        {
            "title": "Microservices Architecture for E-Commerce Platforms",
            "thesis_type": "bachelor",
            "phase": "first_contact",
            "students": [student_ids[1]],
            "supervisors": [supervisor_ids[1]],
            "date_first_contact": (today - timedelta(days=12)).isoformat(),
            "description": "Student interested in cloud-native architectures",
        },

        # Topic Selection - Refining ideas
        {
            "title": "Real-time Data Visualization for IoT Sensor Networks",
            "thesis_type": "master",
            "phase": "topic_selection",
            "students": [student_ids[2]],
            "supervisors": [supervisor_ids[2]],
            "date_first_contact": (today - timedelta(days=45)).isoformat(),
            "date_topic_selected": None,
            "description": "Exploring different visualization frameworks",
        },
        {
            "title": "Comparative Analysis of Graph Databases for Social Networks",
            "thesis_type": "bachelor",
            "phase": "topic_selection",
            "students": [student_ids[3]],
            "supervisors": [supervisor_ids[3]],
            "date_first_contact": (today - timedelta(days=38)).isoformat(),
            "description": "Comparing Neo4j, ArangoDB, and TigerGraph",
        },

        # Registration - Paperwork in progress
        {
            "title": "Mobile App Development with Cross-Platform Frameworks",
            "thesis_type": "bachelor",
            "phase": "registration",
            "students": [student_ids[4]],
            "supervisors": [supervisor_ids[4]],
            "date_first_contact": (today - timedelta(days=75)).isoformat(),
            "date_topic_selected": (today - timedelta(days=30)).isoformat(),
            "description": "Comparing React Native vs Flutter for enterprise apps",
        },
        {
            "title": "Blockchain-based Supply Chain Tracking System",
            "thesis_type": "master",
            "phase": "registration",
            "students": [student_ids[5]],
            "supervisors": [supervisor_ids[1]],
            "date_first_contact": (today - timedelta(days=82)).isoformat(),
            "date_topic_selected": (today - timedelta(days=25)).isoformat(),
            "description": "Implementing smart contracts for supply chain transparency",
        },

        # Working - Active theses
        {
            "title": "Natural Language Processing for Customer Support Automation",
            "thesis_type": "master",
            "phase": "working",
            "students": [student_ids[6]],
            "supervisors": [supervisor_ids[0]],
            "date_first_contact": (today - timedelta(days=120)).isoformat(),
            "date_topic_selected": (today - timedelta(days=75)).isoformat(),
            "date_registration": (today - timedelta(days=45)).isoformat(),
            "date_deadline": (today + timedelta(days=75)).isoformat(),
            "git_repository": "https://github.com/example/nlp-customer-support",
            "description": "Building a chatbot using transformer models",
            "task_description": "Implement and evaluate BERT-based intent classification system",
        },
        {
            "title": "Performance Optimization of Distributed Database Queries",
            "thesis_type": "bachelor",
            "phase": "working",
            "students": [student_ids[7]],
            "supervisors": [supervisor_ids[3]],
            "date_first_contact": (today - timedelta(days=135)).isoformat(),
            "date_topic_selected": (today - timedelta(days=90)).isoformat(),
            "date_registration": (today - timedelta(days=60)).isoformat(),
            "date_deadline": (today + timedelta(days=50)).isoformat(),
            "git_repository": "https://github.com/example/db-query-optimization",
            "description": "Optimizing query performance in PostgreSQL clusters",
        },
        {
            "title": "Computer Vision for Autonomous Drone Navigation",
            "thesis_type": "master",
            "phase": "working",
            "students": [student_ids[8]],
            "supervisors": [supervisor_ids[0]],
            "date_first_contact": (today - timedelta(days=140)).isoformat(),
            "date_topic_selected": (today - timedelta(days=105)).isoformat(),
            "date_registration": (today - timedelta(days=75)).isoformat(),
            "date_deadline": (today + timedelta(days=45)).isoformat(),
            "git_repository": "https://github.com/example/drone-cv",
            "description": "Real-time object detection and path planning",
        },

        # Submitted - Awaiting review
        {
            "title": "Security Analysis of Modern Web Authentication Protocols",
            "thesis_type": "bachelor",
            "phase": "submitted",
            "students": [student_ids[9]],
            "supervisors": [supervisor_ids[1]],
            "date_first_contact": (today - timedelta(days=180)).isoformat(),
            "date_topic_selected": (today - timedelta(days=145)).isoformat(),
            "date_registration": (today - timedelta(days=120)).isoformat(),
            "date_deadline": (today - timedelta(days=10)).isoformat(),
            "date_presentation": (today + timedelta(days=20)).isoformat(),
            "git_repository": "https://github.com/example/web-auth-security",
            "description": "Analysis of OAuth 2.0, OpenID Connect, and WebAuthn",
        },
        {
            "title": "Machine Learning for Stock Price Prediction",
            "thesis_type": "master",
            "phase": "submitted",
            "students": [student_ids[0]],
            "supervisors": [supervisor_ids[2]],
            "date_first_contact": (today - timedelta(days=190)).isoformat(),
            "date_topic_selected": (today - timedelta(days=155)).isoformat(),
            "date_registration": (today - timedelta(days=130)).isoformat(),
            "date_deadline": (today - timedelta(days=5)).isoformat(),
            "date_presentation": (today + timedelta(days=25)).isoformat(),
            "git_repository": "https://github.com/example/ml-stock-prediction",
            "description": "Using LSTM networks for time series forecasting",
        },

        # Under Review
        {
            "title": "Gamification Techniques for Educational Software",
            "thesis_type": "bachelor",
            "phase": "under_review",
            "students": [student_ids[1]],
            "supervisors": [supervisor_ids[4]],
            "date_first_contact": (today - timedelta(days=200)).isoformat(),
            "date_topic_selected": (today - timedelta(days=165)).isoformat(),
            "date_registration": (today - timedelta(days=140)).isoformat(),
            "date_deadline": (today - timedelta(days=45)).isoformat(),
            "date_presentation": (today - timedelta(days=15)).isoformat(),
            "date_review": None,
            "description": "Implementing and evaluating game elements in learning platforms",
        },

        # Final Discussion Scheduled
        {
            "title": "Energy Efficiency in Cloud Computing Infrastructure",
            "thesis_type": "master",
            "phase": "final_discussion_scheduled",
            "students": [student_ids[2]],
            "supervisors": [supervisor_ids[3]],
            "date_first_contact": (today - timedelta(days=210)).isoformat(),
            "date_topic_selected": (today - timedelta(days=175)).isoformat(),
            "date_registration": (today - timedelta(days=150)).isoformat(),
            "date_deadline": (today - timedelta(days=60)).isoformat(),
            "date_presentation": (today - timedelta(days=30)).isoformat(),
            "date_review": (today - timedelta(days=10)).isoformat(),
            "date_final_discussion": (today + timedelta(days=5)).isoformat(),
            "git_repository": "https://github.com/example/cloud-energy-efficiency",
            "description": "Analyzing power consumption patterns and optimization strategies",
            "review": "Very good work. Some minor revisions needed in the conclusion section.",
        },

        # Completed
        {
            "title": "Augmented Reality Applications for Museum Exhibitions",
            "thesis_type": "bachelor",
            "phase": "completed",
            "students": [student_ids[3]],
            "supervisors": [supervisor_ids[4]],
            "date_first_contact": (today - timedelta(days=220)).isoformat(),
            "date_topic_selected": (today - timedelta(days=185)).isoformat(),
            "date_registration": (today - timedelta(days=160)).isoformat(),
            "date_deadline": (today - timedelta(days=90)).isoformat(),
            "date_presentation": (today - timedelta(days=60)).isoformat(),
            "date_review": (today - timedelta(days=40)).isoformat(),
            "date_final_discussion": (today - timedelta(days=20)).isoformat(),
            "git_repository": "https://github.com/example/ar-museum",
            "description": "Unity-based AR app for interactive historical exhibits",
            "review": "Excellent thesis with practical implementation and thorough evaluation. Grade: 1.3",
        },
        {
            "title": "Automated Testing Strategies for Continuous Integration Pipelines",
            "thesis_type": "bachelor",
            "phase": "completed",
            "students": [student_ids[4]],
            "supervisors": [supervisor_ids[1]],
            "date_first_contact": (today - timedelta(days=230)).isoformat(),
            "date_topic_selected": (today - timedelta(days=195)).isoformat(),
            "date_registration": (today - timedelta(days=170)).isoformat(),
            "date_deadline": (today - timedelta(days=100)).isoformat(),
            "date_presentation": (today - timedelta(days=70)).isoformat(),
            "date_review": (today - timedelta(days=50)).isoformat(),
            "date_final_discussion": (today - timedelta(days=30)).isoformat(),
            "git_repository": "https://github.com/example/ci-testing",
            "description": "Comparing test automation frameworks in CI/CD environments",
            "review": "Good work with comprehensive benchmarks. Grade: 1.7",
        },
    ]

    return theses

def generate_demo_comments(thesis_id: int, phase: str) -> List[Dict[str, str]]:
    """Generate appropriate comments based on thesis phase."""
    comments = []

    if phase in ["first_contact", "topic_selection"]:
        comments.append({
            "text": "Initial meeting held. Discussed potential topics and research directions.",
            "is_auto_generated": False
        })

    if phase in ["topic_selection", "registration", "working", "submitted", "under_review", "final_discussion_scheduled", "completed"]:
        comments.append({
            "text": "Topic finalized. Literature review in progress.",
            "is_auto_generated": False
        })

    if phase in ["working", "submitted", "under_review", "final_discussion_scheduled", "completed"]:
        comments.extend([
            {
                "text": "First implementation milestone reached. Initial results look promising.",
                "is_auto_generated": False
            },
            {
                "text": "Regular progress meeting. Discussed methodology and next steps.",
                "is_auto_generated": False
            },
        ])

    if phase in ["submitted", "under_review", "final_discussion_scheduled", "completed"]:
        comments.append({
            "text": "Thesis submitted. Writing quality is good, implementation is solid.",
            "is_auto_generated": False
        })

    if phase in ["under_review", "final_discussion_scheduled", "completed"]:
        comments.append({
            "text": "Review completed. Provided detailed feedback on improvements needed.",
            "is_auto_generated": False
        })

    if phase == "completed":
        comments.append({
            "text": "Final discussion completed successfully. Congratulations!",
            "is_auto_generated": False
        })

    return comments


def populate_demo_data(url: Optional[str] = None, token: Optional[str] = None):
    """Main function to populate demo data."""
    client = ThesisManagerDemoClient(url=url, token=token)

    logger.info("=" * 60)
    logger.info("Starting Demo Data Population")
    logger.info("=" * 60)

    # Create students
    logger.info("\n>>> Creating students...")
    created_students = []
    for student_data in DEMO_STUDENTS:
        student = client.create_student(student_data)
        if student:
            created_students.append(student)

    if not created_students:
        logger.error("Failed to create any students. Aborting.")
        return False

    logger.info("Successfully created %d students", len(created_students))
    student_ids = [s['id'] for s in created_students]

    # Create supervisors
    logger.info("\n>>> Creating supervisors...")
    created_supervisors = []
    for supervisor_data in DEMO_SUPERVISORS:
        supervisor = client.create_supervisor(supervisor_data)
        if supervisor:
            created_supervisors.append(supervisor)

    if not created_supervisors:
        logger.error("Failed to create any supervisors. Aborting.")
        return False

    logger.info("Successfully created %d supervisors", len(created_supervisors))
    supervisor_ids = [s['id'] for s in created_supervisors]

    # Create theses
    logger.info("\n>>> Creating theses...")
    theses_data = generate_demo_theses(student_ids, supervisor_ids)
    created_theses = []

    for thesis_data in theses_data:
        thesis = client.create_thesis(thesis_data)
        if thesis:
            created_theses.append(thesis)

            # Add comments for this thesis
            comments = generate_demo_comments(thesis['id'], thesis['phase'])
            for comment_data in comments:
                client.add_comment(
                    thesis['id'],
                    comment_data['text'],
                    comment_data['is_auto_generated']
                )

    logger.info("Successfully created %d theses", len(created_theses))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Demo Data Population Complete!")
    logger.info("=" * 60)
    logger.info("Created:")
    logger.info("  - %d students", len(created_students))
    logger.info("  - %d supervisors", len(created_supervisors))
    logger.info("  - %d theses", len(created_theses))

    # Phase distribution
    phase_counts = {}
    for thesis in created_theses:
        phase = thesis['phase']
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    logger.info("\nTheses by phase:")
    for phase, count in sorted(phase_counts.items()):
        logger.info("  - %s: %d", phase, count)

    logger.info("\nYou can now view the demo data at: %s", client.url)

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Populate Thesis Manager with demo data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--url',
        help='Thesis Manager URL (overrides environment variable)'
    )
    parser.add_argument(
        '--token',
        help='API token (overrides environment variable)'
    )

    args = parser.parse_args()

    # Confirmation prompt
    if not args.yes:
        print("\nThis script will create demo data in your Thesis Manager instance.")
        print("This includes students, supervisors, theses, and comments.")
        print("\nIMPORTANT: This is intended for demonstration purposes only.")
        print("Do NOT run this on a production system with real data!")
        response = input("\nDo you want to continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted.")
            return 1

    try:
        success = populate_demo_data(url=args.url, token=args.token)
        return 0 if success else 1
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        return 1
    except KeyboardInterrupt:
        logger.info("\nAborted by user")
        return 1
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

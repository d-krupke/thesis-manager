#!/usr/bin/env python3
"""
Quick test script for AI report generator.
"""

import os
import sys
import dotenv
from utils.ai_report_generator import AIReportGenerator, ProgressAnalysis

dotenv.load_dotenv(dotenv.find_dotenv())

# Test data
test_commits = [
    {
        'sha': 'abc123',
        'short': 'abc123',
        'title': 'Implemented core solver algorithm',
        'author': 'Test Student',
        'email': 'student@example.com',
        'date': '2025-10-27 12:00:00',
        'additions': 150,
        'deletions': 20,
        'files': ['src/solver.py', 'src/algorithm.py'],
        'branches': {'main'},
    },
    {
        'sha': 'def456',
        'short': 'def456',
        'title': 'Updated thesis chapter 3',
        'author': 'Test Student',
        'email': 'student@example.com',
        'date': '2025-10-26 15:30:00',
        'additions': 80,
        'deletions': 10,
        'files': ['thesis/chapter3.tex'],
        'branches': {'main'},
    },
]

test_thesis = {
    'id': 1,
    'title': 'Test Thesis',
    'phase': 'working',
    'date_registration': '2025-08-01',
    'date_deadline': '2025-12-01',
}

def test_ai_generator():
    """Test AI report generator initialization and basic functionality."""
    print("Testing AI Report Generator...")
    print(f"OpenAI API Key: {'Set' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")

    try:
        # Initialize
        generator = AIReportGenerator(model='gpt-4o-mini')

        if not generator.agent:
            print("❌ Agent not initialized (API key missing?)")
            return False

        print("✓ Agent initialized successfully")

        # Test analysis
        print("\nRunning test analysis...")
        analysis = generator._analyze_progress(test_commits, test_thesis, 7)

        print("\n✓ Analysis successful!")
        print(f"\nResults:")
        print(f"  Summary: {analysis.summary}")
        print(f"  Code Score: {analysis.code_progress_score}/10")
        print(f"  Thesis Score: {analysis.thesis_progress_score}/10")
        print(f"  Needs Attention: {analysis.needs_attention}")
        print(f"  Reasoning: {analysis.reasoning}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ai_generator()
    sys.exit(0 if success else 1)

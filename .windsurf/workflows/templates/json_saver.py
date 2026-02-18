#!/usr/bin/env python3
"""
JSON Data Saver - Saves PR review analysis data to JSON file

Handles serialization of analysis results to file for downstream
report generation (HTML, JIRA, CLI).
"""

import json
import sys
import os
from pathlib import Path


def save_json_data(json_data, output_file=None, pr_number=None):
    """
    Save JSON analysis data to file with proper serialization.

    Args:
        json_data: Dictionary containing analysis results
        output_file: Optional output file path (default: .ai-review/pr-{pr_number}-data.json)
        pr_number: PR number for default file naming

    Returns:
        (success: bool, message: str, file_path: str)
    """
    try:
        # Determine output file path
        if not output_file:
            if not pr_number:
                raise ValueError("Either output_file or pr_number must be provided")
            output_file = f".ai-review/pr-{pr_number}-data.json"

        # Ensure output directory exists
        output_dir = os.path.dirname(output_file) or '.'
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Serialize JSON data to string with proper formatting
        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)

        # Write to file with UTF-8 encoding (no BOM)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_string)

        file_size = os.path.getsize(output_file)
        message = f"✅ JSON saved: {output_file}\n   File size: {file_size} bytes"

        return True, message, output_file

    except Exception as e:
        message = f"❌ Error saving JSON: {e}"
        return False, message, output_file


def main():
    """Command line interface for saving JSON data"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Save PR review analysis data to JSON file"
    )
    parser.add_argument('--pr', type=str, default='-', help='PR number (or "-" to read from stdin)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    parser.add_argument('--data', type=str, help='JSON data as string (optional)')

    args = parser.parse_args()

    try:
        # Determine PR number
        pr_number = None
        if args.pr == '-':
            # Read PR number from first line of stdin
            first_line = sys.stdin.readline().strip()
            try:
                pr_number = int(first_line)
            except ValueError:
                # If not a number, treat as JSON data
                import io
                sys.stdin = io.StringIO(first_line + '\n' + sys.stdin.read())
                pr_number = None
        else:
            try:
                pr_number = int(args.pr)
            except ValueError:
                pr_number = None

        # If data provided as argument, use it; otherwise read from stdin
        if args.data:
            json_data = json.loads(args.data)
        else:
            # Read JSON from stdin (piped from previous step)
            json_data = json.load(sys.stdin)

        # If PR number not found in args, try to extract from JSON
        if pr_number is None:
            pr_number = json_data.get('pr_number')
            if pr_number is None:
                raise ValueError("PR number not provided and not found in JSON data")

        success, message, file_path = save_json_data(
            json_data,
            output_file=args.output,
            pr_number=pr_number
        )

        print(message)

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

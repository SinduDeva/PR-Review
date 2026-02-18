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


def validate_json_data(json_data):
    """Validate JSON data has minimum required fields"""
    if not isinstance(json_data, dict):
        raise ValueError(f"JSON data must be a dictionary, got {type(json_data).__name__}")

    # Check for at least one of these required fields
    required_fields = ['metadata', 'pr_number', 'findings', 'summary']
    has_field = any(field in json_data for field in required_fields)

    if not has_field:
        raise ValueError(f"JSON data missing required fields. Expected at least one of: {required_fields}")

    return True


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
        if args.pr != '-':
            try:
                pr_number = int(args.pr)
            except ValueError:
                # If not a number, use as-is (might be extracted from JSON later)
                pass

        # If data provided as argument, use it; otherwise read from stdin
        if args.data:
            try:
                json_data = json.loads(args.data)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --data argument: {e}")
                print(f"   Position {e.pos}: {e.msg}")
                sys.exit(1)
        else:
            # Read JSON from stdin (piped from previous step)
            try:
                stdin_content = sys.stdin.read().strip()

                if not stdin_content:
                    raise ValueError("No JSON data received from stdin")

                # Try to parse as JSON
                json_data = json.loads(stdin_content)

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON received from stdin: {e}")
                print(f"   Position {e.pos}: {e.msg}")
                print(f"   Context: {stdin_content[max(0, e.pos-40):min(len(stdin_content), e.pos+40)]}")
                sys.exit(1)
            except ValueError as e:
                print(f"❌ Error reading from stdin: {e}")
                sys.exit(1)

        # Validate JSON structure
        try:
            validate_json_data(json_data)
        except ValueError as e:
            print(f"⚠️  Warning: {e}")
            print("   Continuing anyway (some fields may be missing)")

        # If PR number not found in args, try to extract from JSON
        if pr_number is None:
            pr_number = json_data.get('pr_number')

            # Try nested location
            if pr_number is None:
                metadata = json_data.get('metadata', {})
                pr_number = metadata.get('pr_number')

            if pr_number is None:
                print("⚠️  Warning: PR number not provided and not found in JSON data")
                print("   Using default: pr_unknown")
                pr_number = 'unknown'

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

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

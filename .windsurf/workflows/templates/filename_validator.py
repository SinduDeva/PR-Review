#!/usr/bin/env python3
"""
Validates that all generated files follow standard naming convention.
Standard: pr-{number}-{type}.{ext}
Types: data, full-diff, jira-comment, execution
"""

import sys
import os
import re

VALID_PATTERNS = {
    'json': r'^pr-\d+-data\.json$',
    'html': r'^pr-\d+-data\.html$',
    'txt_jira': r'^pr-\d+-jira-comment\.txt$',
    'txt_diff': r'^pr-\d+-full-diff\.txt$',
    'lock': r'^pr-\d+-execution\.lock$'
}

INVALID_PATTERNS = [
    r'pr-\d+-review-data\.json',    # Legacy format - WRONG
    r'pr-\d+-review\.html',         # Old reference - WRONG
]

def validate_filename(filename, file_type):
    """Validate filename matches standard pattern"""
    pattern = VALID_PATTERNS.get(file_type)
    if not pattern:
        return False, f"Unknown file type: {file_type}"

    basename = os.path.basename(filename)

    # Check against invalid patterns first
    for invalid in INVALID_PATTERNS:
        if re.match(invalid, basename):
            return False, f"Filename uses LEGACY format. Use pr-{{number}}-data.{{ext}} instead."

    # Check against valid pattern
    if not re.match(pattern, basename):
        return False, f"Filename doesn't match pattern: {pattern}"

    return True, "Valid"

def validate_all_files(pr_number):
    """Check all expected files exist with correct names"""
    expected_files = {
        'json': f'.ai-review/pr-{pr_number}-data.json',
        'html': f'.ai-review/pr-{pr_number}-data.html',
        'txt_jira': f'.ai-review/pr-{pr_number}-jira-comment.txt',
    }

    errors = []
    for file_type, filepath in expected_files.items():
        valid, message = validate_filename(filepath, file_type)
        if not valid:
            errors.append(f"❌ {filepath}: {message}")
        elif os.path.exists(filepath):
            print(f"✅ {filepath}: Exists and valid")
        else:
            print(f"⚠️  {filepath}: Valid name but file missing")

    if errors:
        print("\n".join(errors))
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python filename_validator.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]
    if validate_all_files(pr_number):
        print(f"\n✅ All files for PR #{pr_number} use correct naming convention")
        sys.exit(0)
    else:
        print(f"\n❌ Filename validation failed for PR #{pr_number}")
        sys.exit(1)

#!/usr/bin/env python3
"""
JSON Schema Validator for PR Review Analysis Data

Validates that analysis JSON conforms to expected structure
before saving or using in downstream processes.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


class AnalysisDataValidator:
    """Validates PR review analysis JSON data"""

    # Minimum required fields for valid analysis data
    REQUIRED_ROOT_FIELDS = [
        'metadata',           # PR metadata (pr_number, author, etc.)
        'summary',            # Summary metrics (files_changed, issues found, etc.)
        'findings',           # Code findings/issues
    ]

    OPTIONAL_ROOT_FIELDS = [
        'files_reviewed',     # List of reviewed files
        'spring_boot_validation',  # Spring Boot checks
        'test_coverage',      # Test coverage analysis
        'impact_analysis',    # API/dependency impact
        'api_changes',        # API breaking/non-breaking changes
        'overall_recommendation',  # Review recommendation
        'execution_status',   # Workflow execution status
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if not self.verbose and level == "INFO":
            return

        if level == "INFO":
            prefix = "ℹ️"
        elif level == "SUCCESS":
            prefix = "✅"
        elif level == "ERROR":
            prefix = "❌"
        elif level == "WARNING":
            prefix = "⚠️"
        else:
            prefix = "→"

        print(f"{prefix} {message}")

    def validate(self, data: Any) -> Tuple[bool, List[str], List[str]]:
        """
        Validate analysis data structure

        Returns:
            (is_valid: bool, errors: list, warnings: list)
        """
        self.errors = []
        self.warnings = []

        # Check if data is a dictionary
        if not isinstance(data, dict):
            self.errors.append(f"Data must be a dictionary, got {type(data).__name__}")
            return False, self.errors, self.warnings

        self.log("Validating analysis data structure...", "INFO")

        # Check required fields
        self._validate_required_fields(data)

        # Check known fields
        self._validate_known_fields(data)

        # Validate nested structures
        if not self.errors:  # Only if no critical errors
            self._validate_metadata(data.get('metadata', {}))
            self._validate_summary(data.get('summary', {}))
            self._validate_findings(data.get('findings', []))
            self._validate_files_reviewed(data.get('files_reviewed', []))
            self._validate_impact_analysis(data.get('impact_analysis', {}))

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_required_fields(self, data: Dict) -> None:
        """Check all required fields are present"""
        for field in self.REQUIRED_ROOT_FIELDS:
            if field not in data:
                self.errors.append(f"Missing required field: '{field}'")
                self.log(f"Missing required field: '{field}'", "ERROR")
            else:
                self.log(f"✓ Found required field: '{field}'", "INFO")

    def _validate_known_fields(self, data: Dict) -> None:
        """Check for unknown fields (informational)"""
        known = set(self.REQUIRED_ROOT_FIELDS + self.OPTIONAL_ROOT_FIELDS)
        unknown = set(data.keys()) - known

        if unknown:
            msg = f"Unknown fields in data: {', '.join(sorted(unknown))}"
            self.log(msg, "INFO")

    def _validate_metadata(self, metadata: Dict) -> None:
        """Validate metadata structure"""
        required_meta = ['pr_number']
        for field in required_meta:
            if field not in metadata:
                self.warnings.append(f"metadata missing '{field}'")

        # Validate pr_number is numeric
        if 'pr_number' in metadata:
            pr_num = metadata['pr_number']
            try:
                int(pr_num) if isinstance(pr_num, str) else None
            except (ValueError, TypeError):
                self.errors.append(f"pr_number must be numeric, got {pr_num}")

    def _validate_summary(self, summary: Dict) -> None:
        """Validate summary metrics"""
        expected_keys = [
            'files_changed', 'critical_issues', 'high_issues',
            'medium_issues', 'low_issues'
        ]

        for key in expected_keys:
            if key not in summary:
                self.warnings.append(f"summary missing '{key}'")
            else:
                value = summary[key]
                if not isinstance(value, int):
                    try:
                        int(str(value))
                    except (ValueError, TypeError):
                        self.errors.append(f"summary['{key}'] must be numeric")

    def _validate_findings(self, findings: Any) -> None:
        """Validate findings list"""
        if not isinstance(findings, list):
            self.errors.append(f"findings must be a list, got {type(findings).__name__}")
            return

        for idx, finding in enumerate(findings):
            if not isinstance(finding, dict):
                self.errors.append(f"findings[{idx}] must be dict, got {type(finding).__name__}")
                continue

            required_finding_fields = ['severity', 'title']
            for field in required_finding_fields:
                if field not in finding:
                    self.warnings.append(f"findings[{idx}] missing '{field}'")

            # Validate severity
            if 'severity' in finding:
                severity = finding['severity']
                if severity not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    self.warnings.append(
                        f"findings[{idx}]['severity'] has unusual value: {severity}"
                    )

    def _validate_files_reviewed(self, files: Any) -> None:
        """Validate files_reviewed list"""
        if not isinstance(files, list):
            self.warnings.append(f"files_reviewed should be a list")
            return

        for idx, file in enumerate(files):
            if not isinstance(file, dict):
                self.warnings.append(f"files_reviewed[{idx}] should be dict")
                continue

            if 'path' not in file:
                self.warnings.append(f"files_reviewed[{idx}] missing 'path'")

    def _validate_impact_analysis(self, impact: Dict) -> None:
        """Validate impact analysis structure"""
        if not isinstance(impact, dict):
            return

        # Check for expected keys
        if 'affected_apis' in impact:
            if not isinstance(impact['affected_apis'], list):
                self.warnings.append("impact_analysis['affected_apis'] should be a list")

        if 'dependency_graph' in impact:
            graph = impact['dependency_graph']
            if not isinstance(graph, dict):
                self.warnings.append("impact_analysis['dependency_graph'] should be a dict")
            else:
                if 'nodes' in graph and not isinstance(graph['nodes'], list):
                    self.warnings.append("dependency_graph['nodes'] should be a list")
                if 'edges' in graph and not isinstance(graph['edges'], (list, dict)):
                    self.warnings.append("dependency_graph['edges'] should be list or dict")


def validate_file(file_path: str, verbose: bool = False) -> bool:
    """Validate JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON file: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    validator = AnalysisDataValidator(verbose=verbose)
    is_valid, errors, warnings = validator.validate(data)

    print(f"\n{'='*80}")
    print(f"JSON Validation Report: {file_path}")
    print(f"{'='*80}\n")

    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
        print()

    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
        print()

    if is_valid and not warnings:
        print("✅ JSON is VALID and complete")
    elif is_valid:
        print("✅ JSON is VALID but has warnings")
    else:
        print("❌ JSON is INVALID")

    print(f"\n{'='*80}\n")

    return is_valid


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate PR review analysis JSON data"
    )
    parser.add_argument('file', help='JSON file to validate')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    is_valid = validate_file(args.file, verbose=args.verbose)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
JSON Schema Validator for PR Review Output
Ensures consistent JSON structure and format across all workflow runs.
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

class PRReviewSchema:
    """Defines the required JSON schema for PR review output"""

    # Required top-level fields
    REQUIRED_FIELDS = [
        'metadata',
        'summary',
        'findings',
        'files_reviewed',
        'files_skipped',
        'impact_analysis',
        'api_changes',
        'spring_boot_validation',
        'test_coverage',
        'overall_recommendation',
        'execution_status'
    ]

    # Required metadata fields
    METADATA_REQUIRED = [
        'pr_number',
        'title',
        'author',
        'reviewer',
        'source_branch',
        'target_branch',
        'branch',
        'jira_tickets',
        'review_date',
        'review_id'
    ]

    # Summary field requirements
    SUMMARY_REQUIRED = [
        'files_changed',
        'files_validated',
        'files_excluded',
        'lines_added',
        'lines_deleted',
        'critical_issues',
        'high_issues',
        'medium_issues',
        'low_issues',
        'bugs_detected',
        'test_coverage_overall'
    ]

    # Finding structure
    FINDING_REQUIRED = [
        'id',
        'severity',
        'type',
        'title',
        'file',
        'line',
        'description',
        'impact'
    ]

    # Impact analysis structure
    IMPACT_ANALYSIS_REQUIRED = [
        'summary',
        'by_layer',
        'dependency_graph',
        'affected_apis',
        'affected_functionalities',
        'recommendations'
    ]

    # Execution status structure
    EXECUTION_STATUS_REQUIRED = [
        'overall_status',
        'total_steps',
        'successful_steps',
        'failed_steps',
        'steps',
        'warnings',
        'final_message'
    ]


def validate_json_structure(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate JSON structure against schema.

    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["Root must be a JSON object"]

    # Check required top-level fields
    for field in PRReviewSchema.REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate metadata
    if 'metadata' in data:
        metadata = data['metadata']
        if not isinstance(metadata, dict):
            errors.append("Field 'metadata' must be an object")
        else:
            for req_field in PRReviewSchema.METADATA_REQUIRED:
                if req_field not in metadata:
                    errors.append(f"Missing required metadata field: {req_field}")

    # Validate summary
    if 'summary' in data:
        summary = data['summary']
        if not isinstance(summary, dict):
            errors.append("Field 'summary' must be an object")
        else:
            for req_field in PRReviewSchema.SUMMARY_REQUIRED:
                if req_field not in summary:
                    errors.append(f"Missing required summary field: {req_field}")

    # Validate findings is array
    if 'findings' in data:
        findings = data['findings']
        if not isinstance(findings, list):
            errors.append("Field 'findings' must be an array")
        else:
            for idx, finding in enumerate(findings):
                if not isinstance(finding, dict):
                    errors.append(f"Finding {idx} must be an object")
                else:
                    for req_field in PRReviewSchema.FINDING_REQUIRED:
                        if req_field not in finding:
                            errors.append(f"Finding {idx} missing required field: {req_field}")

    # Validate files_reviewed is array
    if 'files_reviewed' in data:
        files = data['files_reviewed']
        if not isinstance(files, list):
            errors.append("Field 'files_reviewed' must be an array")

    # Validate files_skipped is array
    if 'files_skipped' in data:
        files = data['files_skipped']
        if not isinstance(files, list):
            errors.append("Field 'files_skipped' must be an array")

    # Validate impact_analysis
    if 'impact_analysis' in data:
        impact = data['impact_analysis']
        if not isinstance(impact, dict):
            errors.append("Field 'impact_analysis' must be an object")
        else:
            for req_field in PRReviewSchema.IMPACT_ANALYSIS_REQUIRED:
                if req_field not in impact:
                    errors.append(f"Missing required impact_analysis field: {req_field}")

    # Validate api_changes is array
    if 'api_changes' in data:
        api_changes = data['api_changes']
        if not isinstance(api_changes, list):
            errors.append("Field 'api_changes' must be an array")

    # Validate execution_status
    if 'execution_status' in data:
        exec_status = data['execution_status']
        if not isinstance(exec_status, dict):
            errors.append("Field 'execution_status' must be an object")
        else:
            for req_field in PRReviewSchema.EXECUTION_STATUS_REQUIRED:
                if req_field not in exec_status:
                    errors.append(f"Missing required execution_status field: {req_field}")

    return len(errors) == 0, errors


def create_default_json_structure(pr_number: str, pr_title: str = "Unknown PR") -> Dict:
    """
    Create a default JSON structure with all required fields.
    This ensures consistent output even if analysis steps fail.
    """
    return {
        "metadata": {
            "pr_number": pr_number,
            "title": pr_title,
            "author": "Unknown",
            "reviewer": "Claude AI Assistant",
            "source_branch": "Unknown",
            "target_branch": "Unknown",
            "branch": "Unknown → Unknown",
            "jira_tickets": [],
            "jira_warning": None,
            "review_date": datetime.now().strftime('%Y-%m-%d'),
            "workflow_start_time": datetime.now().isoformat(),
            "workflow_end_time": None,
            "execution_time_seconds": 0,
            "review_id": f"PR-{pr_number}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        },
        "pagination_metadata": {
            "method": "unknown",
            "pages_fetched": 0,
            "total_items_retrieved": 0,
            "items_per_page": 0,
            "truncated": False,
            "max_pages_reached": False,
            "warnings": [],
            "api_calls_made": []
        },
        "summary": {
            "files_changed": 0,
            "files_validated": 0,
            "files_excluded": 0,
            "lines_added": 0,
            "lines_deleted": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "bugs_detected": 0,
            "test_coverage": "N/A",
            "test_coverage_overall": "N/A"
        },
        "findings": [],
        "files_reviewed": [],
        "files_skipped": [],
        "impact_analysis": {
            "summary": {
                "files_changed": 0,
                "direct_impact": 0,
                "transitive_impact": 0,
                "total_affected": 0,
                "risk_level": "LOW"
            },
            "by_layer": {
                "CONTROLLER": 0,
                "SERVICE": 0,
                "REPOSITORY": 0,
                "MODEL": 0,
                "UTILITY": 0
            },
            "dependency_graph": {
                "nodes": [],
                "edges": []
            },
            "affected_apis": [],
            "affected_functionalities": [],
            "recommendations": []
        },
        "api_changes": [],
        "spring_boot_validation": {
            "architecture": {
                "score": 0,
                "status": "UNKNOWN",
                "issues": []
            },
            "security": {
                "score": 0,
                "status": "UNKNOWN",
                "issues": []
            },
            "performance": {
                "score": 0,
                "status": "UNKNOWN",
                "issues": []
            },
            "transactions": {
                "score": 0,
                "status": "UNKNOWN",
                "issues": []
            }
        },
        "test_coverage": {
            "overall": "N/A",
            "overall_status": "UNKNOWN",
            "by_type": {
                "unit": "N/A",
                "integration": "N/A",
                "e2e": "N/A"
            },
            "gaps": []
        },
        "overall_recommendation": {
            "decision": "UNABLE_TO_REVIEW",
            "reason": "Analysis could not be completed",
            "must_fix": [],
            "should_fix": []
        },
        "recommendations": [],
        "positive_observations": [],
        "ai_summary": "Unable to generate AI summary at this time",
        "execution_status": {
            "overall_status": "incomplete",
            "total_steps": 7,
            "successful_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "steps": {},
            "warnings": [],
            "final_message": "Workflow execution incomplete"
        }
    }


def merge_partial_json(base_json: Dict, new_data: Dict, preserve_existing: bool = True) -> Dict:
    """
    Safely merge new data into base JSON structure.

    Args:
        base_json: The default/base JSON structure
        new_data: New data to merge
        preserve_existing: If True, keep existing values if new_data is None/empty

    Returns:
        Merged JSON structure
    """
    result = base_json.copy()

    for key, value in new_data.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                # Merge dictionaries recursively
                result[key] = {**result[key], **value}
            elif isinstance(result[key], list) and isinstance(value, list):
                # For lists, append new items if they're not empty
                if value:
                    result[key] = value
            elif value is not None or not preserve_existing:
                # Replace with new value if not None or if we're not preserving
                result[key] = value
        else:
            result[key] = value

    return result


def ensure_json_integrity(json_data: Dict) -> Tuple[Dict, List[str]]:
    """
    Ensure JSON integrity by validating and fixing structure if needed.

    Returns:
        (cleaned_json: Dict, errors_found: List[str])
    """
    errors = []

    # Validate structure
    is_valid, validation_errors = validate_json_structure(json_data)

    if not is_valid:
        errors.extend(validation_errors)

        # Try to repair with defaults
        pr_number = json_data.get('metadata', {}).get('pr_number', 'unknown')
        pr_title = json_data.get('metadata', {}).get('title', 'Unknown PR')

        base = create_default_json_structure(pr_number, pr_title)
        json_data = merge_partial_json(base, json_data)

    return json_data, errors


def save_validated_json(data: Dict, output_file: str, overwrite: bool = True) -> bool:
    """
    Save validated JSON to file.

    Returns:
        True if successful, False otherwise
    """
    try:
        cleaned_data, errors = ensure_json_integrity(data)

        if errors:
            print(f"⚠️ JSON validation warnings ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Validated JSON saved: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python json_schema_validator.py <json_file> [--fix]")
        sys.exit(1)

    json_file = sys.argv[1]
    fix_mode = '--fix' in sys.argv

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        is_valid, errors = validate_json_structure(data)

        if is_valid:
            print(f"✅ JSON structure is valid")
        else:
            print(f"❌ JSON structure has {len(errors)} errors:")
            for error in errors:
                print(f"  - {error}")

            if fix_mode:
                print("\n🔧 Attempting to fix...")
                cleaned, errors_fixed = ensure_json_integrity(data)
                save_validated_json(cleaned, json_file + '.fixed')
                print(f"✅ Fixed JSON saved to: {json_file}.fixed")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Centralized Metadata Schema Constants

Single source of truth for all PR Review workflow metadata definitions.
This module ensures:
- Consistent metadata structure across all runs
- Named constants prevent typos in field access
- Easy schema maintenance and evolution
- Workflow never reads itself (imports from templates instead)
"""

from typing import Dict, List, Any
from datetime import datetime


class MetadataFieldNames:
    """Named constants for metadata field names (prevents string typos)"""

    # Required metadata fields
    PR_NUMBER = 'pr_number'
    TITLE = 'title'
    AUTHOR = 'author'
    REVIEWER = 'reviewer'
    SOURCE_BRANCH = 'source_branch'
    TARGET_BRANCH = 'target_branch'
    BRANCH = 'branch'
    JIRA_TICKETS = 'jira_tickets'
    JIRA_TICKET_ID = 'jira_ticket_id'  # Primary ticket extracted from branch name
    REVIEW_DATE = 'review_date'
    REVIEW_ID = 'review_id'

    # Optional metadata fields
    JIRA_WARNING = 'jira_warning'
    WORKFLOW_START_TIME = 'workflow_start_time'
    WORKFLOW_END_TIME = 'workflow_end_time'
    EXECUTION_TIME_SECONDS = 'execution_time_seconds'


class MetadataSchema:
    """Authoritative metadata schema definition"""

    # All required metadata fields
    REQUIRED_FIELDS = [
        MetadataFieldNames.PR_NUMBER,
        MetadataFieldNames.TITLE,
        MetadataFieldNames.AUTHOR,
        MetadataFieldNames.REVIEWER,
        MetadataFieldNames.SOURCE_BRANCH,
        MetadataFieldNames.TARGET_BRANCH,
        MetadataFieldNames.BRANCH,
        MetadataFieldNames.JIRA_TICKETS,
        MetadataFieldNames.JIRA_TICKET_ID,  # Primary ticket from branch name
        MetadataFieldNames.REVIEW_DATE,
        MetadataFieldNames.REVIEW_ID,
    ]

    # Optional metadata fields
    OPTIONAL_FIELDS = [
        MetadataFieldNames.JIRA_WARNING,
        MetadataFieldNames.WORKFLOW_START_TIME,
        MetadataFieldNames.WORKFLOW_END_TIME,
        MetadataFieldNames.EXECUTION_TIME_SECONDS,
    ]

    # All metadata fields
    ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

    # Field types for validation
    FIELD_TYPES = {
        MetadataFieldNames.PR_NUMBER: str,
        MetadataFieldNames.TITLE: str,
        MetadataFieldNames.AUTHOR: str,
        MetadataFieldNames.REVIEWER: str,
        MetadataFieldNames.SOURCE_BRANCH: str,
        MetadataFieldNames.TARGET_BRANCH: str,
        MetadataFieldNames.BRANCH: str,
        MetadataFieldNames.JIRA_TICKETS: list,
        MetadataFieldNames.JIRA_TICKET_ID: (str, type(None)),  # Can be None if not found
        MetadataFieldNames.REVIEW_DATE: str,
        MetadataFieldNames.REVIEW_ID: str,
        MetadataFieldNames.JIRA_WARNING: (str, type(None)),
        MetadataFieldNames.WORKFLOW_START_TIME: str,
        MetadataFieldNames.WORKFLOW_END_TIME: (str, type(None)),
        MetadataFieldNames.EXECUTION_TIME_SECONDS: (int, float),
    }

    # Default values for each field
    DEFAULTS = {
        MetadataFieldNames.AUTHOR: 'Unknown',
        MetadataFieldNames.REVIEWER: 'Automated Review System',
        MetadataFieldNames.SOURCE_BRANCH: 'Unknown',
        MetadataFieldNames.TARGET_BRANCH: 'Unknown',
        MetadataFieldNames.JIRA_TICKETS: [],
        MetadataFieldNames.JIRA_TICKET_ID: None,  # Will be extracted from branch name
        MetadataFieldNames.JIRA_WARNING: None,
        MetadataFieldNames.EXECUTION_TIME_SECONDS: 0,
    }

    # Field descriptions (for documentation)
    DESCRIPTIONS = {
        MetadataFieldNames.PR_NUMBER: 'Pull request number from repository',
        MetadataFieldNames.TITLE: 'PR title as shown in repository',
        MetadataFieldNames.AUTHOR: 'PR author username',
        MetadataFieldNames.REVIEWER: 'Name of the review tool/process',
        MetadataFieldNames.SOURCE_BRANCH: 'Source branch (feature branch)',
        MetadataFieldNames.TARGET_BRANCH: 'Target branch (typically main/master)',
        MetadataFieldNames.BRANCH: 'Display string: "source → target"',
        MetadataFieldNames.JIRA_TICKETS: 'List of JIRA ticket IDs referenced in PR',
        MetadataFieldNames.REVIEW_DATE: 'Date review was performed (YYYY-MM-DD)',
        MetadataFieldNames.REVIEW_ID: 'Unique identifier for this review run',
        MetadataFieldNames.JIRA_WARNING: 'Warning message if JIRA integration had issues',
        MetadataFieldNames.WORKFLOW_START_TIME: 'ISO timestamp when workflow started',
        MetadataFieldNames.WORKFLOW_END_TIME: 'ISO timestamp when workflow completed',
        MetadataFieldNames.EXECUTION_TIME_SECONDS: 'Total execution time in seconds',
    }


class TopLevelSchema:
    """Schema for top-level JSON sections"""

    # All required top-level sections
    REQUIRED_SECTIONS = [
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
        'execution_status',
    ]

    # Optional sections
    OPTIONAL_SECTIONS = [
        'pagination_metadata',
        'recommendations',
        'positive_observations',
        'ai_summary',
    ]

    # Expected types for each section
    SECTION_TYPES = {
        'metadata': dict,
        'summary': dict,
        'findings': list,
        'files_reviewed': list,
        'files_skipped': list,
        'impact_analysis': dict,
        'api_changes': list,
        'spring_boot_validation': dict,
        'test_coverage': dict,
        'overall_recommendation': dict,
        'execution_status': dict,
        'pagination_metadata': dict,
        'recommendations': list,
        'positive_observations': list,
        'ai_summary': str,
    }


# ===== Factory Functions =====

def create_default_metadata(pr_number: str, pr_title: str = "Unknown PR") -> Dict:
    """
    Create default metadata dictionary with all required and optional fields.

    Args:
        pr_number: PR number/ID
        pr_title: PR title

    Returns:
        Complete metadata dictionary with defaults
    """
    now = datetime.now()

    return {
        MetadataFieldNames.PR_NUMBER: pr_number,
        MetadataFieldNames.TITLE: pr_title,
        MetadataFieldNames.AUTHOR: MetadataSchema.DEFAULTS[MetadataFieldNames.AUTHOR],
        MetadataFieldNames.REVIEWER: MetadataSchema.DEFAULTS[MetadataFieldNames.REVIEWER],
        MetadataFieldNames.SOURCE_BRANCH: MetadataSchema.DEFAULTS[MetadataFieldNames.SOURCE_BRANCH],
        MetadataFieldNames.TARGET_BRANCH: MetadataSchema.DEFAULTS[MetadataFieldNames.TARGET_BRANCH],
        MetadataFieldNames.BRANCH: f"{MetadataSchema.DEFAULTS[MetadataFieldNames.SOURCE_BRANCH]} → {MetadataSchema.DEFAULTS[MetadataFieldNames.TARGET_BRANCH]}",
        MetadataFieldNames.JIRA_TICKETS: [],
        MetadataFieldNames.REVIEW_DATE: now.strftime('%Y-%m-%d'),
        MetadataFieldNames.WORKFLOW_START_TIME: now.isoformat(),
        MetadataFieldNames.WORKFLOW_END_TIME: None,
        MetadataFieldNames.JIRA_WARNING: None,
        MetadataFieldNames.EXECUTION_TIME_SECONDS: 0,
        MetadataFieldNames.REVIEW_ID: f"PR-{pr_number}-{now.strftime('%Y%m%d-%H%M%S')}",
    }


def create_default_json_structure(pr_number: str, pr_title: str = "Unknown PR") -> Dict:
    """
    Create complete default JSON structure with all required sections.

    Args:
        pr_number: PR number/ID
        pr_title: PR title

    Returns:
        Complete JSON structure with all sections filled with defaults
    """
    return {
        'metadata': create_default_metadata(pr_number, pr_title),
        'pagination_metadata': {
            'method': 'unknown',
            'pages_fetched': 0,
            'total_items_retrieved': 0,
            'items_per_page': 0,
            'truncated': False,
            'max_pages_reached': False,
            'warnings': [],
            'api_calls_made': []
        },
        'summary': {
            'files_changed': 0,
            'files_validated': 0,
            'files_excluded': 0,
            'lines_added': 0,
            'lines_deleted': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'bugs_detected': 0,
            'test_coverage': 'N/A',
            'test_coverage_overall': 'N/A'
        },
        'findings': [],
        'files_reviewed': [],
        'files_skipped': [],
        'impact_analysis': {
            'summary': {
                'files_changed': 0,
                'direct_impact': 0,
                'transitive_impact': 0,
                'total_affected': 0,
                'risk_level': 'LOW'
            },
            'by_layer': {
                'CONTROLLER': 0,
                'SERVICE': 0,
                'REPOSITORY': 0,
                'MODEL': 0,
                'UTILITY': 0
            },
            'dependency_graph': {
                'nodes': [],
                'edges': []
            },
            'affected_apis': [],
            'affected_functionalities': [],
            'recommendations': []
        },
        'api_changes': [],
        'spring_boot_validation': {
            'architecture': {
                'score': 0,
                'status': 'UNKNOWN',
                'issues': []
            },
            'security': {
                'score': 0,
                'status': 'UNKNOWN',
                'issues': []
            },
            'performance': {
                'score': 0,
                'status': 'UNKNOWN',
                'issues': []
            },
            'transactions': {
                'score': 0,
                'status': 'UNKNOWN',
                'issues': []
            }
        },
        'test_coverage': {
            'overall': 'N/A',
            'overall_status': 'UNKNOWN',
            'by_type': {
                'unit': 'N/A',
                'integration': 'N/A',
                'e2e': 'N/A'
            },
            'gaps': []
        },
        'overall_recommendation': {
            'decision': 'UNABLE_TO_REVIEW',
            'reason': 'Analysis could not be completed',
            'must_fix': [],
            'should_fix': []
        },
        'recommendations': [],
        'positive_observations': [],
        'ai_summary': 'Unable to generate AI summary at this time',
        'execution_status': {
            'overall_status': 'incomplete',
            'total_steps': 7,
            'successful_steps': 0,
            'failed_steps': 0,
            'skipped_steps': 0,
            'steps': {},
            'warnings': [],
            'final_message': 'Workflow execution incomplete'
        }
    }


def merge_metadata(base: Dict, overrides: Dict, preserve_existing: bool = True) -> Dict:
    """
    Safely merge metadata overrides into base metadata.

    Args:
        base: Base metadata dictionary
        overrides: New values to merge
        preserve_existing: If True, keep existing values if override is None/empty

    Returns:
        Merged metadata dictionary
    """
    result = base.copy()

    for key, value in overrides.items():
        if key in result:
            if value is not None or not preserve_existing:
                result[key] = value
        else:
            result[key] = value

    return result


# ===== Validation Functions =====

def validate_metadata_fields(data: Dict) -> tuple[bool, List[str]]:
    """
    Validate that metadata has all required fields.

    Args:
        data: Dictionary containing metadata

    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["Metadata must be a dictionary"]

    # Check required fields
    for field in MetadataSchema.REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required metadata field: {field}")

    # Check field types
    for field, expected_type in MetadataSchema.FIELD_TYPES.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field}' has wrong type. "
                    f"Expected {expected_type}, got {type(value).__name__}"
                )

    return len(errors) == 0, errors


def is_metadata_complete(data: Dict) -> bool:
    """Check if metadata has all required fields."""
    is_valid, _ = validate_metadata_fields(data)
    return is_valid


def get_missing_fields(data: Dict) -> List[str]:
    """Get list of missing required metadata fields."""
    missing = []

    if not isinstance(data, dict):
        return MetadataSchema.REQUIRED_FIELDS

    for field in MetadataSchema.REQUIRED_FIELDS:
        if field not in data:
            missing.append(field)

    return missing


def get_field_description(field_name: str) -> str:
    """Get human-readable description for a metadata field."""
    return MetadataSchema.DESCRIPTIONS.get(
        field_name,
        f"No description available for field: {field_name}"
    )


def get_all_field_info() -> Dict[str, Dict[str, Any]]:
    """Get complete information about all metadata fields."""
    info = {}

    for field in MetadataSchema.ALL_FIELDS:
        required = field in MetadataSchema.REQUIRED_FIELDS
        optional = field in MetadataSchema.OPTIONAL_FIELDS

        info[field] = {
            'required': required,
            'optional': optional,
            'type': str(MetadataSchema.FIELD_TYPES.get(field, 'unknown')),
            'default': MetadataSchema.DEFAULTS.get(field),
            'description': get_field_description(field)
        }

    return info


if __name__ == '__main__':
    # Test usage
    print("=== Metadata Constants Module ===\n")

    # Print schema info
    print(f"Required fields ({len(MetadataSchema.REQUIRED_FIELDS)}):")
    for field in MetadataSchema.REQUIRED_FIELDS:
        print(f"  - {field}")

    print(f"\nOptional fields ({len(MetadataSchema.OPTIONAL_FIELDS)}):")
    for field in MetadataSchema.OPTIONAL_FIELDS:
        print(f"  - {field}")

    # Test factory function
    print("\n=== Creating Default Metadata ===")
    metadata = create_default_metadata("123", "Test PR")
    print(f"PR Number: {metadata[MetadataFieldNames.PR_NUMBER]}")
    print(f"Title: {metadata[MetadataFieldNames.TITLE]}")
    print(f"Author: {metadata[MetadataFieldNames.AUTHOR]}")
    print(f"Review ID: {metadata[MetadataFieldNames.REVIEW_ID]}")

    # Test validation
    print("\n=== Validating Metadata ===")
    is_valid, errors = validate_metadata_fields(metadata)
    print(f"Valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    print("\n✅ Metadata constants module ready for use")

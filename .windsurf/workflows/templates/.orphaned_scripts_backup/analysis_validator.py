#!/usr/bin/env python3
"""
Analysis Completion Validator
Ensures all required analysis steps are completed before report generation
"""

def validate_analysis_completion(analysis_data):
    """
    Validate that all required analysis fields are populated.

    Args:
        analysis_data: Dict with analysis results from workflow

    Returns:
        Tuple[bool, List[str]] - (is_complete, list of missing fields)
    """
    missing_fields = []

    # CRITICAL FIELDS - Must exist
    critical_fields = [
        ('metadata', 'PR metadata'),
        ('summary', 'Summary of findings'),
        ('findings', 'Code analysis findings'),
        ('overall_recommendation', 'Approval recommendation'),
        ('impact_analysis', 'Impact analysis'),
    ]

    for field, description in critical_fields:
        if field not in analysis_data:
            missing_fields.append(f"Missing: {description} ({field})")
        elif not analysis_data[field]:
            if field == 'findings':
                # findings can be empty list (no issues found), that's OK
                pass
            elif field == 'impact_analysis':
                # Can be partially populated
                if 'summary' not in analysis_data[field]:
                    missing_fields.append(f"Incomplete: {description} - missing summary")
            else:
                missing_fields.append(f"Empty: {description} ({field})")

    # METADATA validations
    if 'metadata' in analysis_data:
        metadata = analysis_data['metadata']
        if not metadata.get('pr_number'):
            missing_fields.append("Metadata: Missing PR number")
        if not metadata.get('author'):
            missing_fields.append("Metadata: Missing PR author")
        if not metadata.get('reviewer'):
            missing_fields.append("Metadata: Missing reviewer information")

    # SUMMARY validations
    if 'summary' in analysis_data:
        summary = analysis_data['summary']
        required_summary_fields = [
            'files_changed', 'files_validated', 'critical_issues',
            'high_issues', 'medium_issues', 'low_issues'
        ]
        for field in required_summary_fields:
            if field not in summary or summary[field] is None:
                missing_fields.append(f"Summary: Missing {field}")

    # RECOMMENDATION validations
    if 'overall_recommendation' in analysis_data:
        rec = analysis_data['overall_recommendation']
        if isinstance(rec, dict):
            if not rec.get('decision'):
                missing_fields.append("Recommendation: Missing decision (APPROVE/REQUEST_CHANGES/BLOCK)")
            if not rec.get('reason'):
                missing_fields.append("Recommendation: Missing reason/justification")

    # IMPACT ANALYSIS validations
    if 'impact_analysis' in analysis_data:
        impact = analysis_data['impact_analysis']
        if isinstance(impact, dict) and 'summary' in impact:
            summary = impact['summary']
            if not summary.get('risk_level'):
                missing_fields.append("Impact Analysis: Missing risk_level")

    # OPTIONAL but recommended fields
    optional_fields = [
        ('ai_summary', 'AI-generated summary'),
        ('files_reviewed', 'Detailed file analysis'),
        ('test_coverage', 'Test coverage analysis'),
        ('spring_boot_validation', 'Spring Boot validation'),
        ('api_changes', 'API impact analysis'),
    ]

    warnings = []
    for field, description in optional_fields:
        if field not in analysis_data or not analysis_data[field]:
            warnings.append(f"Optional field missing: {description} ({field})")

    is_complete = len(missing_fields) == 0

    return is_complete, missing_fields, warnings


def get_validation_report(is_complete, missing_fields, warnings):
    """Generate a human-readable validation report"""
    report = []

    if is_complete:
        report.append("✅ ANALYSIS COMPLETE - All required fields present")
        if warnings:
            report.append("\n⚠️ WARNINGS (non-blocking):")
            for warning in warnings:
                report.append(f"  - {warning}")
    else:
        report.append("❌ ANALYSIS INCOMPLETE - Missing required fields:")
        for field in missing_fields:
            report.append(f"  ❌ {field}")
        if warnings:
            report.append("\n⚠️ WARNINGS:")
            for warning in warnings:
                report.append(f"  ⚠️ {warning}")

    return "\n".join(report)


if __name__ == '__main__':
    # Example usage
    test_data = {
        'metadata': {'pr_number': 123, 'author': 'john.doe'},
        'summary': {'critical_issues': 0, 'high_issues': 1},
    }

    is_complete, missing, warnings = validate_analysis_completion(test_data)
    print(get_validation_report(is_complete, missing, warnings))

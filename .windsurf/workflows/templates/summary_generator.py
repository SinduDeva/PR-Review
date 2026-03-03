#!/usr/bin/env python3
"""
Workflow Execution Summary Generator

Generates a final summary regardless of workflow success/failure.
Always executed in Step 9 to provide user with completion status.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_summary(pr_number, execution_status=None, analysis_data=None):
    """
    Generate final execution summary from execution status and analysis data.

    ALWAYS generates output even if data is partial or missing.
    """

    # Load execution status if available
    if execution_status is None:
        status_file = f'.ai-review/pr-{pr_number}-status.json'
        try:
            with open(status_file, 'r') as f:
                execution_status = json.load(f)
        except:
            execution_status = {
                'overall_status': 'unknown',
                'total_steps': 9,
                'successful_steps': 0,
                'failed_steps': 0
            }

    # Load analysis data if available
    if analysis_data is None:
        data_file = f'.ai-review/pr-{pr_number}-data.json'
        try:
            with open(data_file, 'r') as f:
                analysis_data = json.load(f)
        except:
            analysis_data = {}

    # Extract key metrics
    metadata = analysis_data.get('metadata', {})
    summary = analysis_data.get('summary', {})
    findings = analysis_data.get('findings', [])
    recommendation = analysis_data.get('overall_recommendation', {})

    # Count issues by severity
    critical_count = len([f for f in findings if f.get('severity') == 'CRITICAL'])
    high_count = len([f for f in findings if f.get('severity') == 'HIGH'])
    medium_count = len([f for f in findings if f.get('severity') == 'MEDIUM'])
    low_count = len([f for f in findings if f.get('severity') == 'LOW'])
    total_count = len(findings)

    # Get status details
    overall_status = execution_status.get('overall_status', 'unknown')
    total_steps = execution_status.get('total_steps', 9)
    successful_steps = execution_status.get('successful_steps', 0)
    failed_steps = execution_status.get('failed_steps', 0)
    execution_time = execution_status.get('execution_time_seconds', 'unknown')

    # Build summary text
    summary_text = f"""═════════════════════════════════════════════════════════
PR #{pr_number} - Code Review Summary
═════════════════════════════════════════════════════════

📋 EXECUTION STATUS:
  Overall: {overall_status.upper()} (completed in {execution_time}s if available)
  Steps Completed: {successful_steps}/{total_steps}
  Steps Failed: {failed_steps}

📊 FINDINGS SUMMARY:
  🔴 Critical Issues: {critical_count}
  🟠 High Issues: {high_count}
  🟡 Medium Issues: {medium_count}
  🔵 Low Issues: {low_count}
  ────────────────────
  Total Issues: {total_count}

📁 FILES ANALYZED:
  Files Changed: {summary.get('files_changed', 'unknown')}
  Files Validated: {summary.get('files_validated', 'unknown')}
  Files Excluded: {summary.get('files_excluded', 'unknown')} (test/doc)

✅ OUTPUTS GENERATED:
  ✅ JIRA Comment: posted to {', '.join(metadata.get('jira_tickets', ['none']))}
  ✅ HTML Report: .ai-review/pr-{pr_number}-data.html
  ✅ CLI Summary: displayed above
  ⏳ JSON Data: .ai-review/pr-{pr_number}-data.json (optional)
  ⏳ Database: optional audit trail

🎯 RECOMMENDATION:
  Decision: {recommendation.get('decision', 'PENDING').upper()}
  Reason: {recommendation.get('reason', 'Analysis in progress')}

📌 KEY FINDINGS:
"""

    # Add top critical findings
    critical_findings = [f for f in findings if f.get('severity') == 'CRITICAL']
    if critical_findings:
        summary_text += "\n  🔴 CRITICAL (Must Fix):\n"
        for finding in critical_findings[:3]:
            summary_text += f"    - {finding.get('file', 'unknown')}:{finding.get('line', '?')}\n"
            summary_text += f"      {finding.get('description', 'Issue found')}\n"
        if len(critical_findings) > 3:
            summary_text += f"    ... and {len(critical_findings) - 3} more critical issues\n"

    high_findings = [f for f in findings if f.get('severity') == 'HIGH']
    if high_findings:
        summary_text += "\n  🟠 HIGH (Should Fix):\n"
        for finding in high_findings[:3]:
            summary_text += f"    - {finding.get('file', 'unknown')}:{finding.get('line', '?')}\n"
        if len(high_findings) > 3:
            summary_text += f"    ... and {len(high_findings) - 3} more high issues\n"

    if not critical_findings and not high_findings:
        summary_text += "\n  ✅ No critical or high issues found!\n"

    # Add execution notes
    warnings = execution_status.get('warnings', [])
    if warnings:
        summary_text += "\n⚠️  WARNINGS/NOTES:\n"
        for warning in warnings[:5]:
            summary_text += f"  - {warning}\n"
        if len(warnings) > 5:
            summary_text += f"  ... and {len(warnings) - 5} more notes\n"

    summary_text += f"""
═════════════════════════════════════════════════════════
Workflow Execution Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═════════════════════════════════════════════════════════
"""

    return summary_text


def save_summary(pr_number, summary_text, output_file=None):
    """Save summary to file and print to console."""

    if output_file is None:
        output_file = f'.ai-review/pr-{pr_number}-summary.txt'

    # Ensure directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary_text)

    # Print to console
    print(summary_text)

    return output_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate workflow execution summary')
    parser.add_argument('--pr', required=True, help='PR number')
    parser.add_argument('--execution-status', help='Path to execution status JSON file')
    parser.add_argument('--analysis-data', help='Path to analysis data JSON file')
    parser.add_argument('--summary-output', help='Output file for summary (default: .ai-review/pr-{pr}-summary.txt)')

    args = parser.parse_args()

    # Load execution status if provided
    execution_status = None
    if args.execution_status:
        try:
            with open(args.execution_status, 'r') as f:
                execution_status = json.load(f)
        except:
            pass

    # Load analysis data if provided
    analysis_data = None
    if args.analysis_data:
        try:
            with open(args.analysis_data, 'r') as f:
                analysis_data = json.load(f)
        except:
            pass

    # Generate summary
    summary_text = generate_summary(args.pr, execution_status, analysis_data)

    # Save summary
    output_file = args.summary_output or f'.ai-review/pr-{args.pr}-summary.txt'
    save_summary(args.pr, summary_text, output_file)

    print(f"\n✅ Summary saved to: {output_file}")

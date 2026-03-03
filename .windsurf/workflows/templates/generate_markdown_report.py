#!/usr/bin/env python3
"""
Markdown PR Review Report Generator

Generates clean, functional markdown reports focused on PR analysis.
Output: .ai-review/pr-{pr_number}-data.md
"""

import os
from datetime import datetime


def escape_markdown(text):
    """Escape markdown special characters"""
    if not text:
        return ""
    # Escape common markdown special chars
    text = text.replace('\\', '\\\\')
    text = text.replace('`', '\\`')
    text = text.replace('|', '\\|')
    return text


def generate_markdown_report(data):
    """
    Generate markdown report from analysis data.

    FOCUSES ON PR ANALYSIS ONLY:
    - PR metadata (number, author, reviewer)
    - Code analysis findings
    - Files with issues (collapsible via details tags)
    - Spring Boot validation
    - Test coverage
    - API changes
    - Recommendation
    """

    metadata = data.get('metadata', {})
    summary = data.get('summary', {})
    findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
    spring_boot = data.get('spring_boot_validation', {})
    test_coverage = data.get('test_coverage', {})
    api_changes = data.get('api_changes', []) if isinstance(data.get('api_changes'), list) else []
    impact_analysis = data.get('impact_analysis', {})
    files_reviewed = data.get('files_reviewed', []) if isinstance(data.get('files_reviewed'), list) else []
    recommendation = data.get('overall_recommendation', {})

    pr_number = metadata.get('pr_number', 'unknown')
    author = metadata.get('author', 'Unknown')
    reviewer = metadata.get('reviewer', 'Automated Review System')
    created_at = metadata.get('created_at', datetime.now().isoformat())

    # Group findings by file
    findings_by_file = {}
    for finding in findings:
        file_path = finding.get('file', 'unknown')
        if file_path not in findings_by_file:
            findings_by_file[file_path] = []
        findings_by_file[file_path].append(finding)

    # Count issues by severity
    critical = [f for f in findings if f.get('severity') == 'CRITICAL']
    high = [f for f in findings if f.get('severity') == 'HIGH']
    medium = [f for f in findings if f.get('severity') == 'MEDIUM']
    low = [f for f in findings if f.get('severity') == 'LOW']

    # Build markdown
    md = f"""# PR #{pr_number} Code Review

**Author:** {escape_markdown(author)}
**Reviewer:** {escape_markdown(reviewer)}
**Date:** {created_at}

---

## Summary

| Metric | Count |
|--------|-------|
| **Critical Issues** | {len(critical)} |
| **High Issues** | {len(high)} |
| **Medium Issues** | {len(medium)} |
| **Low Issues** | {len(low)} |
| **Total Issues** | {len(findings)} |
| **Files Reviewed** | {len(files_reviewed)} |

---

## Issue Breakdown

"""

    # Severity breakdown with counts
    if critical or high or medium or low:
        md += "### By Severity\n\n"
        if critical:
            md += f"🔴 **Critical ({len(critical)})**: {', '.join([f['file'] for f in critical[:3]])}"
            if len(critical) > 3:
                md += f" + {len(critical) - 3} more"
            md += "\n"
        if high:
            md += f"🟠 **High ({len(high)})**: {', '.join([f['file'] for f in high[:3]])}"
            if len(high) > 3:
                md += f" + {len(high) - 3} more"
            md += "\n"
        if medium:
            md += f"🟡 **Medium ({len(medium)})**: {', '.join([f['file'] for f in medium[:3]])}"
            if len(medium) > 3:
                md += f" + {len(medium) - 3} more"
            md += "\n"
        if low:
            md += f"🔵 **Low ({len(low)})**: {', '.join([f['file'] for f in low[:3]])}"
            if len(low) > 3:
                md += f" + {len(low) - 3} more"
            md += "\n"
        md += "\n"

    # Files with findings (collapsible sections)
    if findings_by_file:
        md += "### Findings by File\n\n"
        for file_path in sorted(findings_by_file.keys()):
            file_findings = findings_by_file[file_path]
            severity_counts = {}
            for f in file_findings:
                sev = f.get('severity', 'UNKNOWN')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            sev_str = ", ".join([f"{sev} ({count})" for sev, count in sorted(severity_counts.items())])

            md += f"<details>\n<summary><code>{escape_markdown(file_path)}</code> ({sev_str})</summary>\n\n"

            for finding in file_findings:
                severity = finding.get('severity', 'UNKNOWN')
                line = finding.get('line', '?')
                description = escape_markdown(finding.get('description', ''))
                issue_type = escape_markdown(finding.get('type', 'Issue'))

                md += f"**{severity}** - Line {line}: {issue_type}\n\n"
                md += f"> {description}\n\n"

                if finding.get('suggested_fix'):
                    md += f"**Suggested Fix:**\n```\n{escape_markdown(finding.get('suggested_fix', ''))}\n```\n\n"

            md += "</details>\n\n"

    # Spring Boot Validation
    if spring_boot:
        md += "## Spring Boot Validation\n\n"
        if spring_boot.get('overall_score'):
            md += f"**Overall Score:** {spring_boot['overall_score']}\n\n"

        if spring_boot.get('issues'):
            for issue in spring_boot['issues'][:5]:
                severity = issue.get('severity', 'INFO')
                msg = escape_markdown(issue.get('message', ''))
                md += f"- **{severity}:** {msg}\n"
            if len(spring_boot['issues']) > 5:
                md += f"- ... and {len(spring_boot['issues']) - 5} more issues\n"
            md += "\n"

    # Test Coverage
    if test_coverage:
        md += "## Test Coverage\n\n"
        if test_coverage.get('coverage_percentage'):
            md += f"**Coverage:** {test_coverage['coverage_percentage']}%\n\n"
        if test_coverage.get('summary'):
            md += f"{escape_markdown(test_coverage['summary'])}\n\n"

    # API Changes
    if api_changes:
        md += "## API Changes\n\n"
        for change in api_changes[:10]:
            endpoint = escape_markdown(change.get('endpoint', 'unknown'))
            method = change.get('method', 'GET')
            impact = escape_markdown(change.get('impact', 'Unknown'))
            md += f"- **{method} {endpoint}:** {impact}\n"
        if len(api_changes) > 10:
            md += f"- ... and {len(api_changes) - 10} more changes\n"
        md += "\n"

    # Impact Analysis
    if impact_analysis:
        md += "## Impact Analysis\n\n"
        if impact_analysis.get('risk_level'):
            md += f"**Risk Level:** {impact_analysis['risk_level']}\n\n"
        if impact_analysis.get('affected_areas'):
            md += "**Affected Areas:**\n"
            for area in impact_analysis['affected_areas'][:5]:
                md += f"- {escape_markdown(area)}\n"
            if len(impact_analysis['affected_areas']) > 5:
                md += f"- ... and {len(impact_analysis['affected_areas']) - 5} more\n"
            md += "\n"
        if impact_analysis.get('dependencies_affected'):
            md += f"**Dependencies Affected:** {impact_analysis['dependencies_affected']}\n\n"

    # Recommendation
    if recommendation:
        md += "## Recommendation\n\n"
        if recommendation.get('decision'):
            decision = escape_markdown(recommendation['decision'])
            md += f"**Decision:** {decision}\n\n"
        if recommendation.get('action_items'):
            md += "**Action Items:**\n"
            for item in recommendation['action_items']:
                md += f"- {escape_markdown(item)}\n"
            md += "\n"
        if recommendation.get('notes'):
            md += f"**Notes:** {escape_markdown(recommendation['notes'])}\n\n"

    # Footer
    md += "---\n\n"
    md += f"*Generated by Automated Code Review System*  \n"
    md += f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    return md


def save_markdown_report(data, filepath):
    """Save markdown report to file"""
    md = generate_markdown_report(data)

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)

    return md


if __name__ == '__main__':
    import json
    import sys

    # Read JSON from stdin
    if not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        data = {}

    # Get PR number from args
    pr_number = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    filepath = f'.ai-review/pr-{pr_number}-data.md'

    save_markdown_report(data, filepath)
    print(f"✅ Markdown report generated: {filepath}")

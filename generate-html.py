#!/usr/bin/env python3
"""Token-Optimized HTML Report Generator

Generates HTML reports from JSON data using external template (Jinja2) - ZERO
LLM tokens used within the template itself.
"""

import json
import os
from datetime import datetime
from copy import deepcopy

from jinja2 import Environment, FileSystemLoader, select_autoescape

def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def infer_file_type(path):
    """Infer file type based on extension/path for UI badges."""
    _, ext = os.path.splitext(path.lower())
    if ext in {'.java'}:
        return 'java'
    if ext in {'.xml'}:
        return 'xml'
    if ext in {'.yml', '.yaml'}:
        return 'yaml'
    if ext in {'.sql'}:
        return 'sql'
    if ext in {'.md'}:
        return 'doc'
    return 'code'


def map_issues_by_file(findings):
    """Group issue data per file for template consumption."""
    issues = {}
    for idx, issue in enumerate(findings, start=1):
        file_path = issue.get('file', 'misc').lower()
        entry = {
            'id': f'ISSUE-{idx}',
            'severity': issue.get('severity', 'MEDIUM').upper(),
            'type': issue.get('type', 'Bug'),
            'line': issue.get('line', 'N/A'),
            'description': issue.get('description', issue.get('title', 'Issue')),
            'impact': issue.get('impact', issue.get('description', 'Needs review')),
            'code': issue.get('code_snippet'),
            'fix': issue.get('suggested_fix') or issue.get('fix'),
        }
        issues.setdefault(file_path, []).append(entry)
    return issues


def build_metadata(data):
    """Merge metadata/pr fields for template header."""
    metadata = deepcopy(data.get('metadata', {}))
    pr = data.get('pr', {})

    metadata.setdefault('pr_number', pr.get('number'))
    metadata.setdefault('title', pr.get('title'))
    metadata.setdefault('author', pr.get('author', 'Unknown'))
    metadata.setdefault('source_branch', pr.get('source_branch', 'N/A'))
    metadata.setdefault('target_branch', pr.get('target_branch', 'N/A'))
    metadata.setdefault('branch', f"{metadata.get('source_branch')} → {metadata.get('target_branch')}")
    metadata.setdefault('review_date', datetime.now().strftime('%Y-%m-%d'))
    metadata.setdefault('execution_time_seconds', pr.get('execution_time_seconds', '—'))
    metadata.setdefault('jira_tickets', pr.get('jira_tickets', []))
    metadata.setdefault('review_id', metadata.get('review_id', f"PR-{pr.get('number', 'N/A')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"))
    return metadata


def build_summary(files_reviewed, files_skipped, critical, high, medium, data):
    additions = sum(f.get('lines_added', 0) for f in files_reviewed)
    deletions = sum(f.get('lines_deleted', 0) for f in files_reviewed)
    summary_data = data.get('summary', {})
    return {
        'files_validated': summary_data.get('files_validated', len(files_reviewed)),
        'files_excluded': summary_data.get('files_excluded', len(files_skipped)),
        'lines_added': summary_data.get('lines_added', additions),
        'lines_deleted': summary_data.get('lines_deleted', deletions),
        'critical_issues': summary_data.get('critical_issues', len(critical)),
        'high_issues': summary_data.get('high_issues', len(high)),
        'bugs_detected': summary_data.get('bugs_detected', len(critical) + len(high) + len(medium)),
        'test_coverage_overall': summary_data.get('test_coverage_overall', data.get('test_coverage', {}).get('overall', 'N/A'))
    }


def build_impact_analysis(files_reviewed, critical, high, data):
    base = deepcopy(data.get('impact_analysis', {}))
    summary = base.get('summary', {})
    summary.setdefault('files_changed', len(files_reviewed))
    summary.setdefault('direct_impact', 'HIGH' if critical else 'MEDIUM' if high else 'LOW')
    summary.setdefault('transitive_impact', summary.get('direct_impact'))
    summary.setdefault('risk_level', summary.get('direct_impact'))
    base['summary'] = summary
    base.setdefault('dependency_graph', None)
    base.setdefault('affected_apis', [])
    return base


def build_files_context(files_reviewed, findings):
    issues_map = map_issues_by_file(findings)
    detailed_files = []
    for file_info in files_reviewed:
        path = file_info.get('path', 'unknown')
        key = path.lower()
        issues = issues_map.get(key, issues_map.get(os.path.basename(key), []))
        additions = file_info.get('lines_added', file_info.get('additions', 0))
        deletions = file_info.get('lines_deleted', file_info.get('deletions', 0))
        validations = {
            'overall_status': 'FAIL' if issues else 'PASS',
            'bugs_detected': len(issues),
            'security_issues': sum(1 for issue in issues if 'security' in (issue['description'] or '').lower()),
            'performance_issues': 0,
            'code_quality': 'PARTIAL' if issues else 'PASS',
            'spring_boot_compliance': 'PASS'
        }
        detailed_files.append({
            'path': path,
            'type': infer_file_type(path),
            'layer': file_info.get('layer'),
            'status': file_info.get('status', 'UPDATED'),
            'additions': additions,
            'deletions': deletions,
            'summary': file_info.get('summary', ''),
            'ai_summary': file_info.get('ai_summary', file_info.get('summary', 'No AI summary provided.')),
            'validations': validations,
            'issues': issues,
            'dependencies': file_info.get('dependencies'),
            'test_coverage': file_info.get('test_coverage')
        })
    return detailed_files


def build_overall_recommendation(critical, high, data):
    recommendation = deepcopy(data.get('overall_recommendation', {}))
    if not recommendation.get('decision'):
        if critical:
            recommendation['decision'] = 'BLOCK'
            recommendation['reason'] = 'Critical issues must be resolved before merge.'
        elif high:
            recommendation['decision'] = 'REQUEST_CHANGES'
            recommendation['reason'] = 'High severity issues detected.'
        else:
            recommendation['decision'] = 'APPROVE'
            recommendation['reason'] = 'No major issues detected.'
    recommendation.setdefault('must_fix', [issue['description'] for issue in critical])
    recommendation.setdefault('should_fix', [issue['description'] for issue in high])
    return recommendation


def generate_html_report(data):
    """
    Generate HTML report from JSON data using external template
    ZERO LLM tokens used - pure Python processing
    """
    template_path = os.path.join(os.path.dirname(__file__), 'pr-review-template.html')
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(template_path)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['basename'] = lambda path: os.path.basename(path) if path else ''

    try:
        template = env.get_template(os.path.basename(template_path))
    except Exception as exc:
        return f"<html><body><h1>Error loading template: {exc}</h1></body></html>"

    findings = data.get('findings', [])
    files_reviewed = data.get('files_reviewed', [])
    files_skipped = data.get('files_skipped', [])

    critical = [f for f in findings if f.get('severity') == 'CRITICAL']
    high = [f for f in findings if f.get('severity') == 'HIGH']
    medium = [f for f in findings if f.get('severity') in {'MEDIUM', 'LOW'}]

    context = {
        'metadata': build_metadata(data),
        'summary': build_summary(files_reviewed, files_skipped, critical, high, medium, data),
        'impact_analysis': build_impact_analysis(files_reviewed, critical, high, data),
        'files_reviewed': build_files_context(files_reviewed, findings),
        'files_excluded': data.get('files_excluded', [{'path': f.get('path', 'unknown'), 'reason': f.get('reason', 'Skipped by workflow')} for f in files_skipped]),
        'spring_boot_validation': data.get('spring_boot_validation'),
        'test_coverage': data.get('test_coverage'),
        'overall_recommendation': build_overall_recommendation(critical, high, data),
        'positive_observations': data.get('positive_observations', []),
        'ai_summary': data.get('ai_summary', 'AI summary not available'),
        'generated_at': data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')),
    }

    try:
        return template.render(**context)
    except Exception as exc:
        return f"<html><body><h1>Error rendering template: {escape_html(str(exc))}</h1></body></html>"

def main():
    """Command line interface for testing"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python generate-html.py <json_data_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    try:
        with open(json_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        html = generate_html_report(data)
        
        # Output HTML
        output_file = json_file.replace('.json', '.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML report generated: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

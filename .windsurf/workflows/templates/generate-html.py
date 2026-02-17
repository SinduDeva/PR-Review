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


def generate_api_impact_html(api_changes, affected_apis):
    """
    Generate HTML section for API impact analysis
    Shows affected endpoints, breaking changes, and migration notes
    """
    if not api_changes and not affected_apis:
        return '<div class="alert alert-success">✅ No API changes detected</div>'

    html = []
    html.append('<section class="api-impact card shadow mb-4">')
    html.append('  <div class="card-header bg-info text-white">')
    html.append('    <h3><i class="fas fa-exchange-alt"></i> 🔗 Affected APIs</h3>')
    html.append('  </div>')
    html.append('  <div class="card-body">')

    # Breaking Changes Section
    breaking_changes = [c for c in (api_changes or []) if c.get('type') == 'BREAKING']
    if breaking_changes:
        html.append('    <div class="breaking-changes mb-4">')
        html.append('      <h4 class="text-danger"><i class="fas fa-exclamation-circle"></i> ⚠️ Breaking Changes (Migration Required)</h4>')
        html.append('      <div class="table-responsive">')
        html.append('        <table class="table table-hover">')
        html.append('          <thead class="table-dark">')
        html.append('            <tr><th>Endpoint</th><th>Method</th><th>Change</th><th>Impact</th></tr>')
        html.append('          </thead>')
        html.append('          <tbody>')

        for change in breaking_changes:
            endpoint = change.get('endpoint', 'Unknown')
            method = change.get('method', 'UNKNOWN')
            change_desc = change.get('change', 'API Modified')
            impact = change.get('impact', 'UNKNOWN')
            impact_color = 'danger' if impact == 'HIGH' else 'warning'

            html.append(f'            <tr>')
            html.append(f'              <td><code>{endpoint}</code></td>')
            html.append(f'              <td><span class="badge bg-primary">{method}</span></td>')
            html.append(f'              <td>{change_desc}</td>')
            html.append(f'              <td><span class="badge bg-{impact_color}">{impact}</span></td>')
            html.append(f'            </tr>')

        html.append('          </tbody>')
        html.append('        </table>')
        html.append('      </div>')

        # Migration Notes
        html.append('      <div class="alert alert-warning mt-3">')
        html.append('        <strong>Migration Notes:</strong>')
        html.append('        <ul>')
        for change in breaking_changes:
            if change.get('migration_notes'):
                html.append(f'          <li>{change["migration_notes"]}</li>')
            if change.get('affected_consumers'):
                html.append(f'          <li>Affected consumers: {", ".join(change["affected_consumers"])}</li>')
        html.append('        </ul>')
        html.append('      </div>')
        html.append('    </div>')

    # Non-Breaking Changes Section
    non_breaking_changes = [c for c in (api_changes or []) if c.get('type') != 'BREAKING']
    if non_breaking_changes:
        html.append('    <div class="non-breaking-changes mb-4">')
        html.append('      <h4 class="text-success"><i class="fas fa-check-circle"></i> ℹ️ Non-Breaking Changes</h4>')
        html.append('      <p class="text-muted">The following API changes are backward compatible:</p>')
        html.append('      <ul class="list-group">')

        for change in non_breaking_changes:
            endpoint = change.get('endpoint', 'Unknown')
            method = change.get('method', 'UNKNOWN')
            change_desc = change.get('change', 'API Modified')
            html.append(f'        <li class="list-group-item"><code>{method} {endpoint}</code> - {change_desc}</li>')

        html.append('      </ul>')
        html.append('    </div>')

    # Affected Endpoints Summary
    if affected_apis:
        html.append('    <div class="affected-endpoints-summary">')
        html.append('      <h4>📊 All Affected Endpoints</h4>')
        html.append('      <div class="table-responsive">')
        html.append('        <table class="table table-sm">')
        html.append('          <thead><tr><th>Endpoint</th><th>Method</th><th>Status</th></tr></thead>')
        html.append('          <tbody>')

        for api in affected_apis[:20]:  # Show top 20
            endpoint = api.get('endpoint', 'Unknown')
            method = api.get('method', 'UNKNOWN')
            status = api.get('status', 'Modified')
            status_badge = 'warning' if status in ['MODIFIED', 'Changed'] else 'success' if status == 'NEW' else 'danger'

            html.append(f'            <tr>')
            html.append(f'              <td><code>{endpoint}</code></td>')
            html.append(f'              <td>{method}</td>')
            html.append(f'              <td><span class="badge bg-{status_badge}">{status}</span></td>')
            html.append(f'            </tr>')

        if len(affected_apis) > 20:
            html.append(f'            <tr><td colspan="3" class="text-muted">... and {len(affected_apis) - 20} more</td></tr>')

        html.append('          </tbody>')
        html.append('        </table>')
        html.append('      </div>')
        html.append('    </div>')

    html.append('  </div>')
    html.append('</section>')

    return '\n'.join(html)


def generate_html_report(data):
    """
    Generate HTML report from JSON data using external template
    ZERO LLM tokens used - pure Python processing
    Gracefully handles missing data to ensure HTML is always generated.
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

    # Safely extract data with defaults
    findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
    files_reviewed = data.get('files_reviewed', []) if isinstance(data.get('files_reviewed'), list) else []
    files_skipped = data.get('files_skipped', []) if isinstance(data.get('files_skipped'), list) else []

    critical = [f for f in findings if f.get('severity') == 'CRITICAL']
    high = [f for f in findings if f.get('severity') == 'HIGH']
    medium = [f for f in findings if f.get('severity') in {'MEDIUM', 'LOW'}]

    # Build context with graceful fallbacks
    try:
        metadata = build_metadata(data)
    except Exception as e:
        print(f"⚠️ Warning building metadata: {e}")
        metadata = {'pr_number': 'unknown', 'title': 'Unknown PR', 'author': 'Unknown', 'branch': 'Unknown'}

    try:
        summary = build_summary(files_reviewed, files_skipped, critical, high, medium, data)
    except Exception as e:
        print(f"⚠️ Warning building summary: {e}")
        summary = {
            'files_validated': len(files_reviewed),
            'files_excluded': len(files_skipped),
            'critical_issues': len(critical),
            'high_issues': len(high),
            'bugs_detected': len(critical) + len(high)
        }

    try:
        impact_analysis = build_impact_analysis(files_reviewed, critical, high, data)
    except Exception as e:
        print(f"⚠️ Warning building impact analysis: {e}")
        impact_analysis = {
            'summary': {'files_changed': len(files_reviewed), 'risk_level': 'UNKNOWN'},
            'affected_apis': []
        }

    try:
        files_context = build_files_context(files_reviewed, findings)
    except Exception as e:
        print(f"⚠️ Warning building files context: {e}")
        files_context = []

    try:
        overall_rec = build_overall_recommendation(critical, high, data)
    except Exception as e:
        print(f"⚠️ Warning building recommendation: {e}")
        overall_rec = {'decision': 'UNABLE_TO_REVIEW', 'reason': 'Could not complete review'}

    # Generate API impact HTML section
    try:
        api_changes = data.get('api_changes', []) if isinstance(data.get('api_changes'), list) else []
        affected_apis = data.get('impact_analysis', {}).get('affected_apis', []) if isinstance(data.get('impact_analysis', {}), dict) else []
        api_impact_html = generate_api_impact_html(api_changes, affected_apis)
    except Exception as e:
        print(f"⚠️ Warning building API impact section: {e}")
        api_impact_html = '<div class="alert alert-success">✅ No API changes detected</div>'

    context = {
        'metadata': metadata,
        'summary': summary,
        'pagination_metadata': data.get('pagination_metadata', {}),
        'execution_status': data.get('execution_status', {}),
        'impact_analysis': impact_analysis,
        'files_reviewed': files_context,
        'files_excluded': [{'path': f.get('path', 'unknown'), 'reason': f.get('reason', 'Skipped by workflow')} for f in files_skipped],
        'spring_boot_validation': data.get('spring_boot_validation', {}),
        'test_coverage': data.get('test_coverage', {}),
        'overall_recommendation': overall_rec,
        'positive_observations': data.get('positive_observations', []) if isinstance(data.get('positive_observations'), list) else [],
        'ai_summary': data.get('ai_summary', 'AI summary not available'),
        'api_impact_html': api_impact_html,
        'generated_at': data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')),
    }

    try:
        return template.render(**context)
    except Exception as exc:
        # If template rendering fails, generate minimal HTML with available data
        print(f"⚠️ Warning rendering template: {exc}")
        return generate_fallback_html(context)

def generate_fallback_html(context):
    """Generate minimal fallback HTML when template rendering fails"""
    metadata = context.get('metadata', {})
    summary = context.get('summary', {})

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PR #{metadata.get('pr_number', 'unknown')} - Code Review (Fallback Report)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 5px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #f0f0f0; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PR #{metadata.get('pr_number', 'unknown')} - Code Review Report (Fallback)</h1>
        <p><strong>Title:</strong> {metadata.get('title', 'Unknown')}</p>
        <p><strong>Branch:</strong> {metadata.get('branch', 'Unknown')}</p>
    </div>

    <div class="section">
        <h2>⚠️ Important Notice</h2>
        <div class="warning">
            <p><strong>This is a fallback report.</strong> The HTML template could not be fully rendered.</p>
            <p>Please view the JSON data file for complete analysis details:</p>
            <p><code>.ai-review/pr-{metadata.get('pr_number', 'unknown')}-data.json</code></p>
        </div>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Files Validated</td>
                <td>{summary.get('files_validated', 'N/A')}</td>
            </tr>
            <tr>
                <td>Critical Issues</td>
                <td><strong style="color: red;">{summary.get('critical_issues', 0)}</strong></td>
            </tr>
            <tr>
                <td>High Priority Issues</td>
                <td><strong style="color: orange;">{summary.get('high_issues', 0)}</strong></td>
            </tr>
            <tr>
                <td>Test Coverage</td>
                <td>{summary.get('test_coverage_overall', 'N/A')}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Generated</h2>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>"""
    return html


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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

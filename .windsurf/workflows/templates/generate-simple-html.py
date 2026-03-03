#!/usr/bin/env python3
"""
Simple PR-Focused HTML Report Generator

Generates clean, functional HTML reports focused ONLY on PR analysis.
No enterprise UI, no workflow metadata, no pagination info.
Collapsible file sections with issue details.
"""

import os
from datetime import datetime


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


def generate_simple_html_report(data):
    """
    Generate simple, PR-focused HTML report from analysis data.

    FOCUSES ON PR ANALYSIS ONLY:
    - PR metadata (number, author, reviewer)
    - Code analysis findings
    - Files with issues (collapsible)
    - Spring Boot validation
    - Test coverage
    - API changes
    - Recommendation

    EXCLUDES WORKFLOW METADATA:
    - No pagination info
    - No file detection method
    - No workflow execution times
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

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR #{pr_number} - Code Review</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f9f9f9;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .header {{
            background: #f0f0f0;
            border-bottom: 2px solid #333;
            padding: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            font-size: 14px;
            margin-top: 10px;
        }}
        .meta-item {{
            display: flex;
            justify-content: space-between;
            border: 1px solid #ddd;
            padding: 8px 12px;
            background: #fafafa;
        }}
        .meta-label {{
            font-weight: bold;
            width: 100px;
        }}
        .section {{
            border-bottom: 1px solid #ddd;
            padding: 20px;
        }}
        .section h2 {{
            margin: 0 0 15px 0;
            font-size: 18px;
            border-bottom: 2px solid #eee;
            padding-bottom: 8px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }}
        .summary-box {{
            background: #fafafa;
            border: 1px solid #ddd;
            padding: 15px;
            text-align: center;
        }}
        .summary-number {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }}
        .summary-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .issue-count-critical {{ color: #d32f2f; }}
        .issue-count-high {{ color: #ff6f00; }}
        .issue-count-medium {{ color: #fbc02d; }}
        .issue-count-low {{ color: #1976d2; }}

        .findings-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .finding {{
            background: #fafafa;
            border-left: 4px solid #ddd;
            padding: 12px;
            margin: 8px 0;
            border-radius: 2px;
        }}
        .finding.critical {{
            border-left-color: #d32f2f;
            background: #ffebee;
        }}
        .finding.high {{
            border-left-color: #ff6f00;
            background: #fff3e0;
        }}
        .finding.medium {{
            border-left-color: #fbc02d;
            background: #fffde7;
        }}
        .finding.low {{
            border-left-color: #1976d2;
            background: #e3f2fd;
        }}
        .finding-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: bold;
        }}
        .severity-badge {{
            padding: 2px 8px;
            border-radius: 3px;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }}
        .severity-badge.critical {{ background: #d32f2f; }}
        .severity-badge.high {{ background: #ff6f00; }}
        .severity-badge.medium {{ background: #fbc02d; color: #333; }}
        .severity-badge.low {{ background: #1976d2; }}

        .file-item {{
            background: #f5f5f5;
            border: 1px solid #ddd;
            margin: 8px 0;
            border-radius: 2px;
            overflow: hidden;
        }}
        .file-header {{
            background: #efefef;
            padding: 12px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        }}
        .file-header:hover {{
            background: #e0e0e0;
        }}
        .file-content {{
            padding: 12px;
            display: none;
        }}
        .file-content.open {{
            display: block;
        }}
        .file-issues {{
            margin: 10px 0;
        }}
        .validation-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .validation-table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .validation-table td:first-child {{
            font-weight: bold;
            width: 150px;
        }}
        .score {{
            font-weight: bold;
            font-size: 16px;
        }}
        .score.pass {{ color: #388e3c; }}
        .score.warning {{ color: #ff6f00; }}
        .score.fail {{ color: #d32f2f; }}

        .table-simple {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .table-simple th {{
            background: #f0f0f0;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            font-weight: bold;
        }}
        .table-simple td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .table-simple tr:nth-child(even) {{
            background: #fafafa;
        }}

        .recommendation {{
            background: #e8f5e9;
            border-left: 4px solid #388e3c;
            padding: 15px;
            border-radius: 2px;
            margin: 10px 0;
        }}
        .recommendation.request-changes {{
            background: #fff3e0;
            border-left-color: #ff6f00;
        }}
        .recommendation.block {{
            background: #ffebee;
            border-left-color: #d32f2f;
        }}
        .decision-label {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 8px;
        }}

        .no-issues {{
            color: #388e3c;
            font-weight: bold;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 2px;
        }}

        .footer {{
            background: #f9f9f9;
            border-top: 1px solid #ddd;
            padding: 15px 20px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>PR #{pr_number} - Code Review Report</h1>
        <div class="meta">
            <div class="meta-item"><span class="meta-label">Author:</span> {escape_html(author)}</div>
            <div class="meta-item"><span class="meta-label">Reviewer:</span> {escape_html(reviewer)}</div>
            <div class="meta-item"><span class="meta-label">Review Date:</span> {metadata.get('review_date', 'N/A')}</div>
            <div class="meta-item"><span class="meta-label">Review ID:</span> {escape_html(metadata.get('review_id', 'N/A'))}</div>
        </div>
    </div>

    <!-- SUMMARY -->
    <div class="section">
        <h2>📊 Summary</h2>
        <div class="summary-grid">
            <div class="summary-box">
                <div class="summary-number">{summary.get('files_validated', 0)}</div>
                <div class="summary-label">Files Analyzed</div>
            </div>
            <div class="summary-box">
                <div class="summary-number">{summary.get('lines_added', 0)}</div>
                <div class="summary-label">Lines Added</div>
            </div>
            <div class="summary-box">
                <div class="summary-number">{summary.get('lines_deleted', 0)}</div>
                <div class="summary-label">Lines Deleted</div>
            </div>
            <div class="summary-box">
                <div class="summary-number issue-count-critical">{len(critical)}</div>
                <div class="summary-label">Critical Issues</div>
            </div>
            <div class="summary-box">
                <div class="summary-number issue-count-high">{len(high)}</div>
                <div class="summary-label">High Issues</div>
            </div>
            <div class="summary-box">
                <div class="summary-number">{summary.get('test_coverage', 'N/A')}</div>
                <div class="summary-label">Test Coverage</div>
            </div>
        </div>
    </div>

    <!-- CODE ANALYSIS -->
    <div class="section">
        <h2>🔍 Code Analysis</h2>
        {"<div class='no-issues'>✅ No code analysis issues detected</div>" if not findings else f"""
        <p>Found <strong>{len(findings)}</strong> issues across {len(findings_by_file)} file(s):</p>
        """}

        {f'''
        <div class="file-item">
            <div class="file-header" onclick="this.nextElementSibling.classList.toggle('open')">
                <span>Issues by File</span>
                <span>▼</span>
            </div>
            <div class="file-content">
                {"".join([f'''
                <div class="file-issues">
                    <strong>{escape_html(file_path)}</strong> ({len(issues)} issue{"s" if len(issues) != 1 else ""})
                    <ul class="findings-list">
                        {"".join([f'''
                        <li class="finding {issue.get('severity', 'low').lower()}">
                            <div class="finding-header">
                                <span>{escape_html(issue.get('title', 'Issue'))}</span>
                                <span class="severity-badge {issue.get('severity', 'LOW').lower()}">{issue.get('severity', 'LOW')}</span>
                            </div>
                            <div><strong>File:</strong> {escape_html(issue.get('file', 'unknown'))}:{issue.get('line', 'N/A')}</div>
                            <div><strong>Description:</strong> {escape_html(issue.get('description', 'No description'))}</div>
                            {f"<div><strong>Impact:</strong> {escape_html(issue.get('impact', ''))}</div>" if issue.get('impact') else ""}
                            {f"<div><strong>Fix:</strong> {escape_html(issue.get('suggestion', ''))}</div>" if issue.get('suggestion') else ""}
                        </li>
                        ''' for issue in issues])}
                    </ul>
                </div>
                ''' for file_path, issues in sorted(findings_by_file.items())])}
            </div>
        </div>
        ''' if findings else ""}
    </div>

    <!-- SPRING BOOT VALIDATION -->
    {f'''
    <div class="section">
        <h2>🎯 Spring Boot Validation</h2>
        <table class="validation-table">
            {"".join([f'''
            <tr>
                <td>{category}</td>
                <td>
                    <span class="score {("pass" if score >= 8.0 else "warning" if score >= 6.0 else "fail")}">
                        {score}/10
                    </span>
                </td>
                <td>{"✅ PASS" if score >= 8.0 else "⚠️ WARNING" if score >= 6.0 else "❌ FAIL"}</td>
            </tr>
            {f"<tr><td colspan='3'><small>{', '.join(issues[:2])}</small></td></tr>" if issues and score < 8.0 else ""}
            ''' for category, details in [
                ("Architecture", spring_boot.get('architecture', {})),
                ("Security", spring_boot.get('security', {})),
                ("Performance", spring_boot.get('performance', {})),
                ("Transactions", spring_boot.get('transactions', {}))
            ] for score in [details.get('score', 0)] for issues in [details.get('issues', [])]])}
        </table>
    </div>
    ''' if spring_boot else ""}

    <!-- TEST COVERAGE -->
    {f'''
    <div class="section">
        <h2>📈 Test Coverage</h2>
        <table class="validation-table">
            <tr>
                <td>Overall Coverage</td>
                <td><strong>{test_coverage.get('overall', 'N/A')}</strong></td>
            </tr>
            <tr>
                <td>Unit Tests</td>
                <td>{test_coverage.get('by_type', {}).get('unit', 'N/A')}</td>
            </tr>
            <tr>
                <td>Integration Tests</td>
                <td>{test_coverage.get('by_type', {}).get('integration', 'N/A')}</td>
            </tr>
            <tr>
                <td>E2E Tests</td>
                <td>{test_coverage.get('by_type', {}).get('e2e', 'N/A')}</td>
            </tr>
        </table>
        {f"<p>Coverage Gaps: {len(test_coverage.get('gaps', []))} methods missing tests</p>" if test_coverage.get('gaps') else ""}
    </div>
    ''' if test_coverage else ""}

    <!-- API CHANGES -->
    {f'''
    <div class="section">
        <h2>🔗 API Impact</h2>
        {f'''
        <div>
            <p><strong>Breaking Changes:</strong> {len([c for c in api_changes if c.get('type') == 'BREAKING'])}</p>
            <table class="table-simple">
                <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Change</th>
                    <th>Impact</th>
                </tr>
                {"".join([f'''
                <tr>
                    <td><code>{escape_html(change.get('endpoint', 'Unknown'))}</code></td>
                    <td>{change.get('method', 'UNKNOWN')}</td>
                    <td>{escape_html(change.get('change', 'API modified'))}</td>
                    <td>{change.get('impact', 'UNKNOWN')}</td>
                </tr>
                ''' for change in api_changes[:20]])}
            </table>
        </div>
        ''' if api_changes else "<p>No API changes detected</p>"}
    </div>
    ''' if api_changes else ""}

    <!-- IMPACT ANALYSIS -->
    {f'''
    <div class="section">
        <h2>⚡ Impact Analysis</h2>
        <table class="validation-table">
            <tr>
                <td>Risk Level</td>
                <td><strong>{impact_analysis.get('summary', {}).get('risk_level', 'UNKNOWN')}</strong></td>
            </tr>
            <tr>
                <td>Files Changed</td>
                <td>{impact_analysis.get('summary', {}).get('files_changed', len(files_reviewed))}</td>
            </tr>
            <tr>
                <td>Affected Controllers</td>
                <td>{impact_analysis.get('by_layer', {}).get('CONTROLLER', 0)}</td>
            </tr>
            <tr>
                <td>Affected Services</td>
                <td>{impact_analysis.get('by_layer', {}).get('SERVICE', 0)}</td>
            </tr>
        </table>
    </div>
    ''' if impact_analysis else ""}

    <!-- RECOMMENDATION -->
    <div class="section">
        <h2>✅ Review Recommendation</h2>
        {f'''
        <div class="recommendation {("" if recommendation.get('decision') == 'APPROVE' else "request-changes" if recommendation.get('decision') == 'REQUEST_CHANGES' else "block")}">
            <div class="decision-label">
                {recommendation.get('decision', 'UNABLE_TO_REVIEW')}
            </div>
            <div>{escape_html(recommendation.get('reason', 'No reason provided'))}</div>
            {f'''
            <div style="margin-top: 10px;">
                <strong>Must Fix:</strong>
                <ul>
                    {"".join([f"<li>{escape_html(item)}</li>" for item in recommendation.get('must_fix', [])])}
                </ul>
            </div>
            ''' if recommendation.get('must_fix') else ""}
            {f'''
            <div style="margin-top: 10px;">
                <strong>Should Fix:</strong>
                <ul>
                    {"".join([f"<li>{escape_html(item)}</li>" for item in recommendation.get('should_fix', [])])}
                </ul>
            </div>
            ''' if recommendation.get('should_fix') else ""}
        </div>
        ''' if recommendation else "<p>No recommendation available</p>"}
    </div>

</div>

<div class="footer">
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Review System
</div>
</body>
</html>
"""

    return html


def save_simple_html_report(data, output_file=None):
    """Save generated HTML report to file

    Args:
        data: Dict with analysis results from workflow
        output_file: Optional output path (auto-generated if not provided)

    Returns:
        output_file path if successful, None otherwise
    """
    try:
        html = generate_simple_html_report(data)
    except Exception as e:
        print(f"⚠️ Error generating HTML: {e}")
        html = "<html><body><h1>Error generating report</h1></body></html>"

    # Determine output file
    if not output_file:
        try:
            pr_number = data.get('metadata', {}).get('pr_number', 'unknown')
            output_file = f".ai-review/pr-{pr_number}-data.html"
        except Exception:
            output_file = ".ai-review/pr-unknown-data.html"

    # Save HTML
    try:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML report generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error saving HTML report: {e}")
        return None


if __name__ == '__main__':
    print("This script is designed for workflow integration.")
    print("Import and use: generate_simple_html_report() or save_simple_html_report()")

#!/usr/bin/env python3
"""
HTML Report Generator for PR Code Review Analysis
Generates HTML reports directly from in-memory analysis_data without JSON dependency
"""

import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    text = str(text)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

def get_severity_color(severity):
    """Get color code for severity level"""
    severity_lower = str(severity).lower()
    colors = {
        "critical": "#d32f2f",  # Red
        "high": "#f57c00",      # Orange
        "medium": "#fbc02d",    # Yellow
        "low": "#388e3c",       # Green
    }
    return colors.get(severity_lower, "#9c27b0")  # Purple default

def format_finding(finding):
    """Format a single finding as HTML"""
    if isinstance(finding, dict):
        severity = finding.get("severity", "MEDIUM")
        file_name = finding.get("file", "unknown")
        description = finding.get("description", "No description")
        line = finding.get("line", "")
        fix = finding.get("fix", "")
        impact = finding.get("impact", "")
    else:
        # Handle string format
        severity = "MEDIUM"
        file_name = "unknown"
        description = str(finding)
        line = ""
        fix = ""
        impact = ""

    color = get_severity_color(severity)
    line_str = f" <strong>Line {line}:</strong>" if line else ""

    html = f"""
    <div class="finding" style="border-left: 4px solid {color};">
      <div class="finding-header">
        <span class="severity" style="background-color: {color};">{escape_html(severity)}</span>
        <span class="file">{escape_html(file_name)}{line_str}</span>
      </div>
      <div class="finding-body">
        <p><strong>Issue:</strong> {escape_html(description)}</p>
"""

    if impact:
        html += f'        <p><strong>Impact:</strong> {escape_html(impact)}</p>\n'

    if fix:
        html += f'        <p><strong>Fix:</strong> {escape_html(fix)}</p>\n'

    html += """      </div>
    </div>
"""
    return html

def generate_html_report(analysis_data, output_file):
    """Generate HTML report from analysis_data"""

    # VALIDATION: Ensure ALL analysis data is present (NO SHORTCUTS)
    print("\n" + "="*70)
    print("HTML REPORT GENERATION - VALIDATING ALL ANALYSIS DATA")
    print("="*70)

    required_fields = [
        'pr_number', 'pr_title', 'pr_author', 'pr_source_branch', 'pr_target_branch',
        'files_changed', 'files_validated',
        'findings', 'critical_issues', 'high_issues', 'medium_issues', 'low_issues',
        'api_changes', 'impact_analysis', 'test_coverage',
        'decision', 'decision_reason'
    ]

    missing_fields = []
    for field in required_fields:
        if field not in analysis_data:
            missing_fields.append(field)
            print(f"❌ MISSING: {field}")
        elif analysis_data[field] is None:
            missing_fields.append(field)
            print(f"❌ NULL: {field}")
        else:
            print(f"✅ {field}")

    if missing_fields:
        raise ValueError(f"INCOMPLETE ANALYSIS DATA - Cannot generate HTML. Missing fields: {missing_fields}")

    findings_count = len(analysis_data.get('findings', []))
    print(f"\n✅ Analysis validation passed")
    print(f"   Findings included: {findings_count}")
    print(f"   Critical: {analysis_data.get('critical_issues', 0)}")
    print(f"   High: {analysis_data.get('high_issues', 0)}")
    print(f"   Medium: {analysis_data.get('medium_issues', 0)}")
    print(f"   Low: {analysis_data.get('low_issues', 0)}")
    print("="*70 + "\n")

    # Extract data with safe defaults
    pr_number = analysis_data.get("pr_number", "UNKNOWN")
    pr_title = escape_html(analysis_data.get("pr_title", "Untitled PR"))
    pr_author = escape_html(analysis_data.get("pr_author", "Unknown"))
    pr_source_branch = escape_html(analysis_data.get("pr_source_branch", "unknown"))
    pr_target_branch = escape_html(analysis_data.get("pr_target_branch", "main"))

    files_changed = analysis_data.get("files_changed", 0)
    files_validated = analysis_data.get("files_validated", 0)

    critical_issues = analysis_data.get("critical_issues", 0)
    high_issues = analysis_data.get("high_issues", 0)
    medium_issues = analysis_data.get("medium_issues", 0)
    low_issues = analysis_data.get("low_issues", 0)

    findings = analysis_data.get("findings", [])
    recommendations = analysis_data.get("recommendations", [])
    decision = escape_html(analysis_data.get("decision", "PENDING REVIEW"))
    decision_reason = escape_html(analysis_data.get("decision_reason", "Analysis in progress"))

    api_changes = analysis_data.get("api_changes", [])
    test_coverage = analysis_data.get("test_coverage", {})
    spring_boot_validation = analysis_data.get("spring_boot_validation", {})

    # Generate findings HTML
    findings_html = ""
    if findings and len(findings) > 0:
        for finding in findings:
            findings_html += format_finding(finding)
    else:
        findings_html = '<div class="no-issues"><p>✅ No issues found</p></div>'

    # Generate recommendations HTML
    recommendations_html = ""
    if recommendations and len(recommendations) > 0:
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                rec_text = rec.get("text", str(rec))
            else:
                rec_text = str(rec)
            recommendations_html += f'<li>{escape_html(rec_text)}</li>\n'
    else:
        recommendations_html = '<li>No specific recommendations at this time</li>'

    # Generate API changes HTML
    api_html = ""
    if api_changes and len(api_changes) > 0:
        for api in api_changes:
            if isinstance(api, dict):
                endpoint = escape_html(api.get("endpoint", "unknown"))
                method = escape_html(api.get("method", "GET"))
                change = escape_html(api.get("change", "Modified"))
                impact = escape_html(api.get("impact", ""))
                api_html += f"""
        <div class="api-change">
          <strong>{method} {endpoint}</strong>
          <p><em>{change}</em></p>
"""
                if impact:
                    api_html += f'          <p>Impact: {impact}</p>\n'
                api_html += '        </div>\n'
    else:
        api_html = '<p>No API changes detected</p>'

    # Generate test coverage HTML
    coverage_html = ""
    if test_coverage:
        overall = test_coverage.get("overall", "N/A")
        unit = test_coverage.get("unit", "N/A")
        integration = test_coverage.get("integration", "N/A")
        coverage_html = f"""
        <p><strong>Overall Coverage:</strong> {escape_html(overall)}</p>
        <p><strong>Unit Tests:</strong> {escape_html(unit)}</p>
        <p><strong>Integration Tests:</strong> {escape_html(integration)}</p>
"""
    else:
        coverage_html = "<p>No test coverage data available</p>"

    # Generate Spring Boot validation HTML
    springboot_html = ""
    if spring_boot_validation:
        arch = spring_boot_validation.get("architecture_score", "N/A")
        sec = spring_boot_validation.get("security_score", "N/A")
        perf = spring_boot_validation.get("performance_score", "N/A")
        springboot_html = f"""
        <p><strong>Architecture Score:</strong> {escape_html(arch)}</p>
        <p><strong>Security Score:</strong> {escape_html(sec)}</p>
        <p><strong>Performance Score:</strong> {escape_html(perf)}</p>
"""
    else:
        springboot_html = "<p>No Spring Boot validation data available</p>"

    # Determine decision color
    decision_color = {
        "APPROVE": "#4caf50",
        "REQUEST_CHANGES": "#ff9800",
        "BLOCK": "#d32f2f",
        "PENDING": "#2196f3",
    }.get(decision.upper(), "#9c27b0")

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create HTML document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR #{pr_number} - Code Review Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background-color: #fff;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #1976d2;
            margin-bottom: 10px;
            font-size: 28px;
        }}

        .pr-meta {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
        }}

        .meta-item {{
            padding: 10px;
        }}

        .meta-label {{
            font-weight: bold;
            color: #666;
            margin-bottom: 5px;
        }}

        .meta-value {{
            color: #333;
            word-break: break-all;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }}

        .summary-card {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ccc;
            text-align: center;
        }}

        .summary-card.critical {{
            border-left-color: #d32f2f;
        }}

        .summary-card.high {{
            border-left-color: #f57c00;
        }}

        .summary-card.medium {{
            border-left-color: #fbc02d;
        }}

        .summary-card.low {{
            border-left-color: #388e3c;
        }}

        .summary-number {{
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }}

        .summary-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}

        section {{
            background-color: #fff;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h2 {{
            color: #1976d2;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #1976d2;
        }}

        h3 {{
            color: #333;
            font-size: 16px;
            margin-top: 15px;
            margin-bottom: 10px;
        }}

        .decision {{
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            color: white;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            background-color: {decision_color};
        }}

        .decision-reason {{
            margin-top: 15px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid {decision_color};
            border-radius: 4px;
        }}

        .finding {{
            background-color: #f9f9f9;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #ccc;
        }}

        .finding-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}

        .severity {{
            padding: 4px 12px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .file {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #666;
            flex: 1;
        }}

        .finding-body {{
            margin-top: 10px;
        }}

        .finding-body p {{
            margin: 8px 0;
            font-size: 14px;
        }}

        .no-issues {{
            padding: 30px;
            text-align: center;
            color: #4caf50;
            font-size: 16px;
        }}

        ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}

        li {{
            margin-bottom: 8px;
            line-height: 1.5;
        }}

        .api-change {{
            background-color: #f0f4ff;
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 3px solid #1976d2;
        }}

        .api-change strong {{
            font-family: 'Courier New', monospace;
            color: #1976d2;
        }}

        .api-change p {{
            margin: 5px 0;
            font-size: 13px;
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eee;
            margin-top: 30px;
        }}

        .collapsible {{
            cursor: pointer;
            padding: 15px;
            background-color: #f0f0f0;
            border-radius: 4px;
            margin: 10px 0;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .collapsible:hover {{
            background-color: #e0e0e0;
        }}

        .collapsible.active {{
            background-color: #1976d2;
            color: white;
        }}

        .collapsible-content {{
            display: none;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            margin-top: 5px;
        }}

        .collapsible-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Automated Code Review Analysis</h1>
            <h2 style="color: #666; font-size: 16px; font-weight: normal; margin: 5px 0;">PR #{pr_number}: {pr_title}</h2>

            <div class="pr-meta">
                <div class="meta-item">
                    <div class="meta-label">Author</div>
                    <div class="meta-value">{pr_author}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Branch</div>
                    <div class="meta-value">{pr_source_branch} → {pr_target_branch}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Files Changed</div>
                    <div class="meta-value">{files_changed} changed, {files_validated} validated</div>
                </div>
            </div>

            <div class="summary">
                <div class="summary-card critical">
                    <div class="summary-label">Critical</div>
                    <div class="summary-number">{critical_issues}</div>
                </div>
                <div class="summary-card high">
                    <div class="summary-label">High</div>
                    <div class="summary-number">{high_issues}</div>
                </div>
                <div class="summary-card medium">
                    <div class="summary-label">Medium</div>
                    <div class="summary-number">{medium_issues}</div>
                </div>
                <div class="summary-card low">
                    <div class="summary-label">Low</div>
                    <div class="summary-number">{low_issues}</div>
                </div>
            </div>
        </header>

        <section>
            <h2>📋 Recommendation</h2>
            <div class="decision">{decision}</div>
            <div class="decision-reason">
                <strong>Reason:</strong>
                <p>{decision_reason}</p>
            </div>
        </section>

        <section>
            <h2>🔍 Code Analysis Findings</h2>
            {findings_html}
        </section>

        <section>
            <h2>📊 Test Coverage</h2>
            {coverage_html}
        </section>

        <section>
            <h2>🏗️ Spring Boot Validation</h2>
            {springboot_html}
        </section>

        <section>
            <h2>🔗 API Changes</h2>
            {api_html}
        </section>

        <section>
            <h2>✅ Recommendations</h2>
            <ul>
                {recommendations_html}
            </ul>
        </section>

        <footer>
            <p>Generated on {timestamp} | Automated Code Review System</p>
            <p>This report is auto-generated from code analysis. Manual review recommended for critical changes.</p>
        </footer>
    </div>

    <script>
        // Collapsible sections functionality
        document.querySelectorAll('.collapsible').forEach(btn => {{
            btn.addEventListener('click', function() {{
                this.classList.toggle('active');
                this.nextElementSibling.classList.toggle('active');
            }});
        }});
    </script>
</body>
</html>"""

    # Write HTML file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_file

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python generate_html_report.py <output_file> <pr_number> [open_browser]")
        sys.exit(1)

    output_file = sys.argv[1]
    pr_number = sys.argv[2]
    open_browser = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    # Read analysis_data from stdin or use defaults
    import json
    analysis_data = {}

    # Try to read from stdin (piped data)
    try:
        analysis_data = json.loads(sys.stdin.read())
    except:
        # Use minimal defaults if no data provided
        analysis_data = {
            "pr_number": pr_number,
            "pr_title": f"PR #{pr_number}",
            "pr_author": "Unknown",
            "pr_source_branch": "feature-branch",
            "pr_target_branch": "main",
            "files_changed": 0,
            "files_validated": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "findings": [],
            "decision": "PENDING",
            "decision_reason": "Analysis data not provided",
        }

    # Generate HTML
    print("\n" + "="*70)
    print("GENERATING HTML REPORT FROM IN-MEMORY ANALYSIS DATA")
    print("="*70 + "\n")

    output_path = generate_html_report(analysis_data, output_file)
    print(f"✅ HTML report generated: {output_path}")

    # Verify file was created
    if not os.path.exists(output_path):
        print(f"❌ ERROR: HTML file not created at {output_path}")
        return 1

    file_size = os.path.getsize(output_path)
    print(f"✅ File size: {file_size} bytes (sanity check: complete report)")

    # Open in browser if requested
    if open_browser:
        try:
            browser_url = f"file://{os.path.abspath(output_path)}"
            webbrowser.open(browser_url)
            print(f"✅ AUTO-OPEN: Report opened in default browser")
            print(f"   URL: {browser_url}")
        except Exception as e:
            print(f"⚠️  Could not auto-open browser: {e}")
            print(f"   File available at: {output_path}")
            print(f"   Please open manually in your browser")
    else:
        print(f"✅ Report saved (auto-open disabled)")
        print(f"   Path: {output_path}")

    print("\n" + "="*70)
    print("HTML REPORT GENERATION COMPLETE")
    print("="*70 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
PR-Focused HTML Report Generator

Generates clean HTML reports with:
- Summary metrics at top
- Recommendation section
- Expandable/collapsible files with issues underneath
- Auto-opens HTML in default browser
"""

import os
import json
import sys
import subprocess
import platform
from datetime import datetime
from pathlib import Path


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


def validate_html(html_content):
    """
    Validate HTML structure and content consistency

    Returns: (is_valid, error_message)
    """
    if not html_content or not isinstance(html_content, str):
        return False, "HTML content is empty or invalid type"

    # Check for essential HTML structure
    if not html_content.strip().startswith('<!DOCTYPE'):
        return False, "Missing DOCTYPE declaration"

    if '<html>' not in html_content.lower():
        return False, "Missing <html> tag"

    if '<head>' not in html_content.lower():
        return False, "Missing <head> tag"

    if '<body>' not in html_content.lower():
        return False, "Missing <body> tag"

    # Check for matching closing tags
    open_count = html_content.count('<html')
    close_count = html_content.count('</html>')
    if open_count != close_count:
        return False, "Mismatched <html> tags"

    # Check meta charset
    if 'charset' not in html_content.lower():
        return False, "Missing charset meta tag"

    return True, ""


def generate_fallback_html(pr_number, error_message):
    """
    Generate minimal valid HTML as fallback
    Used when main generation fails
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR #{escape_html(str(pr_number))} - Code Review</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .error {{
            background: #ffebee;
            border: 1px solid #d32f2f;
            border-radius: 4px;
            padding: 20px;
            color: #d32f2f;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PR #{escape_html(str(pr_number))} - Code Review Report</h1>
        <div class="error">
            <strong>⚠️ Report Generation Error</strong>
            <p>{escape_html(str(error_message))}</p>
            <p>The automated review encountered an issue generating the detailed HTML report. However, the analysis has been completed and results are available through other channels (JIRA comments, CLI output).</p>
        </div>
        <div class="footer">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Automated Code Review
        </div>
    </div>
</body>
</html>
"""
    return html


def open_html_in_browser(html_file):
    """
    Auto-open HTML file in default browser with retry logic
    Supports Windows, macOS, Linux, Cascade (cloud IDE), and various shells

    Guaranteed to not block workflow - always returns gracefully
    """
    max_retries = 3
    retry_delay = 1  # seconds

    try:
        html_path = Path(html_file).resolve()

        if not html_path.exists():
            print(f"⚠️  HTML file not found: {html_path}")
            return False

        system = platform.system()

        # Detect if running in Cascade (cloud IDE)
        in_cascade = os.environ.get('WINDSURF_WORKSPACE') or os.environ.get('WINDSURF_PROJECT')

        try:
            if in_cascade:
                # Cascade/Cloud IDE: Print file URL for user to open
                print(f"✅ HTML report generated: {html_path}")
                print(f"📖 Open in browser: file://{html_path}")
                # Try to open anyway, will fail gracefully
                for attempt in range(max_retries):
                    try:
                        import webbrowser
                        webbrowser.open(f'file://{html_path}')
                        return True
                    except Exception as e:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                        else:
                            pass
                return True

            elif system == "Windows":
                # Windows: use start or explorer with retry
                for attempt in range(max_retries):
                    try:
                        os.startfile(str(html_path))
                        print(f"✅ Opening in default browser: {html_path}")
                        return True
                    except Exception:
                        try:
                            subprocess.Popen(['explorer', str(html_path)])
                            print(f"✅ Opening in default browser: {html_path}")
                            return True
                        except Exception as e:
                            if attempt < max_retries - 1:
                                import time
                                time.sleep(retry_delay)
                return False

            elif system == "Darwin":
                # macOS: use open command with retry
                for attempt in range(max_retries):
                    try:
                        subprocess.Popen(['open', str(html_path)])
                        print(f"✅ Opening in default browser: {html_path}")
                        return True
                    except Exception as e:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                return False

            else:
                # Linux: try xdg-open, then fallback options with retry
                for attempt in range(max_retries):
                    try:
                        xdg_open_exists = subprocess.run(['which', 'xdg-open'], capture_output=True).returncode == 0

                        if xdg_open_exists:
                            subprocess.Popen(['xdg-open', str(html_path)])
                            print(f"✅ Opening in default browser: {html_path}")
                            return True

                        # Fallback: try common browsers
                        browsers = ['firefox', 'chromium', 'google-chrome', 'brave', 'opera']
                        for browser in browsers:
                            try:
                                subprocess.Popen([browser, str(html_path)])
                                print(f"✅ Opening in {browser}: {html_path}")
                                return True
                            except:
                                continue
                    except Exception as e:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                        else:
                            break

                print(f"⚠️  Could not auto-open browser. View manually: {html_path}")
                return False

        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print(f"   View manually: {html_path}")
            return False

    except Exception as e:
        print(f"⚠️  Error opening HTML: {e}")
        return False


def generate_simple_html_report(data):
    """Generate HTML report with expandable file sections and all required analysis sections"""

    metadata = data.get('metadata', {})
    summary = data.get('summary', {})
    findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
    recommendation = data.get('overall_recommendation', {})
    spring_boot = data.get('spring_boot_validation', {})
    test_coverage = data.get('test_coverage', {})
    api_changes = data.get('api_changes', []) if isinstance(data.get('api_changes'), list) else []
    impact_analysis = data.get('impact_analysis', {})
    positive_obs = data.get('positive_observations', {})
    ai_summary = data.get('ai_summary', {})

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

    # Determine recommendation style
    rec_decision = recommendation.get('decision', 'UNABLE_TO_REVIEW')
    rec_class = 'approve' if rec_decision == 'APPROVE' else 'request-changes' if rec_decision == 'REQUEST_CHANGES' else 'block'
    rec_icon = '✅' if rec_decision == 'APPROVE' else '⚠️' if rec_decision == 'REQUEST_CHANGES' else '❌'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR #{pr_number} - Code Review</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header-meta {{
            display: flex;
            gap: 20px;
            font-size: 14px;
            opacity: 0.95;
        }}
        .header-meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        /* Summary Section */
        .section {{
            border-bottom: 1px solid #eee;
            padding: 30px;
        }}
        .section h2 {{
            margin: 0 0 20px 0;
            font-size: 20px;
            color: #333;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }}
        .metric-box {{
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            text-align: center;
        }}
        .metric-number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-box.critical .metric-number {{ color: #d32f2f; }}
        .metric-box.high .metric-number {{ color: #ff6f00; }}
        .metric-box.medium .metric-number {{ color: #fbc02d; }}
        .metric-box.low .metric-number {{ color: #1976d2; }}

        /* Recommendation */
        .recommendation {{
            background: #e8f5e9;
            border-left: 4px solid #388e3c;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .recommendation.request-changes {{
            background: #fff3e0;
            border-left-color: #ff6f00;
        }}
        .recommendation.block {{
            background: #ffebee;
            border-left-color: #d32f2f;
        }}
        .rec-header {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .rec-reason {{
            font-size: 14px;
            line-height: 1.6;
            margin: 10px 0;
        }}
        .rec-items {{
            margin-top: 15px;
        }}
        .rec-items strong {{
            display: block;
            margin: 10px 0 5px 0;
        }}
        .rec-items ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}

        /* Files Section */
        .files-container {{
            margin-top: 20px;
        }}
        .file-item {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 8px 0;
            overflow: hidden;
        }}
        .file-header {{
            background: #f5f5f5;
            padding: 15px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
            transition: background 0.2s;
        }}
        .file-header:hover {{
            background: #efefef;
        }}
        .file-path {{
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .file-count {{
            background: #667eea;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 10px;
        }}
        .file-toggle {{
            color: #666;
            font-size: 18px;
        }}
        .file-content {{
            display: none;
            padding: 15px;
            border-top: 1px solid #eee;
            background: #fafafa;
        }}
        .file-content.open {{
            display: block;
        }}

        /* Issues */
        .finding {{
            background: white;
            border-left: 4px solid #ddd;
            padding: 12px;
            margin: 8px 0;
            border-radius: 2px;
            font-size: 13px;
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
        .finding-title {{
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .severity-badge {{
            padding: 2px 8px;
            border-radius: 3px;
            color: white;
            font-size: 11px;
            font-weight: bold;
        }}
        .severity-badge.critical {{ background: #d32f2f; }}
        .severity-badge.high {{ background: #ff6f00; }}
        .severity-badge.medium {{ background: #fbc02d; color: #333; }}
        .severity-badge.low {{ background: #1976d2; }}
        .finding-detail {{
            margin: 6px 0;
            font-size: 12px;
        }}
        .finding-detail strong {{
            display: inline-block;
            width: 80px;
        }}
        .finding-detail pre {{
            background: #f5f5f5;
            padding: 8px;
            border-radius: 3px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            margin: 6px 0;
        }}
        .finding-detail code {{
            color: #333;
        }}

        /* Other Sections */
        .no-issues {{
            color: #388e3c;
            font-weight: bold;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 4px;
            text-align: center;
        }}
        .validation-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .validation-table td {{
            padding: 12px;
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

        .footer {{
            background: #f9f9f9;
            border-top: 1px solid #ddd;
            padding: 15px 30px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
    <script>
        function toggleFile(element) {{
            const content = element.nextElementSibling;
            const toggle = element.querySelector('.file-toggle');
            content.classList.toggle('open');
            toggle.textContent = content.classList.contains('open') ? '▼' : '▶';
        }}
    </script>
</head>
<body>
<div class="container">
    <!-- HEADER -->
    <div class="header">
        <h1>PR #{pr_number} - Code Review</h1>
        <div class="header-meta">
            <div class="header-meta-item">👤 Author: {escape_html(author)}</div>
            <div class="header-meta-item">👁️ Reviewer: {escape_html(reviewer)}</div>
            <div class="header-meta-item">📅 {metadata.get('review_date', 'N/A')}</div>
        </div>
    </div>

    <!-- SUMMARY -->
    <div class="section">
        <h2>📊 Summary</h2>
        <div class="summary-grid">
            <div class="metric-box">
                <div class="metric-number">{summary.get('files_validated', 0)}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-box">
                <div class="metric-number">{summary.get('lines_added', 0)}</div>
                <div class="metric-label">Lines Added</div>
            </div>
            <div class="metric-box">
                <div class="metric-number">{summary.get('lines_deleted', 0)}</div>
                <div class="metric-label">Lines Deleted</div>
            </div>
            <div class="metric-box critical">
                <div class="metric-number">{len(critical)}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-box high">
                <div class="metric-number">{len(high)}</div>
                <div class="metric-label">High</div>
            </div>
            <div class="metric-box medium">
                <div class="metric-number">{len(medium)}</div>
                <div class="metric-label">Medium</div>
            </div>
            <div class="metric-box low">
                <div class="metric-number">{len(low)}</div>
                <div class="metric-label">Low</div>
            </div>
        </div>
    </div>

    <!-- RECOMMENDATION -->
    <div class="section">
        <h2>✅ Review Recommendation</h2>
        <div class="recommendation {rec_class}">
            <div class="rec-header">{rec_icon} {escape_html(rec_decision)}</div>
            <div class="rec-reason">{escape_html(recommendation.get('reason', 'No reason provided'))}</div>
            {f'''
            <div class="rec-items">
                <strong>Must Fix:</strong>
                <ul>
                    {"".join([f"<li>{escape_html(item)}</li>" for item in recommendation.get('must_fix', [])])}
                </ul>
            </div>
            ''' if recommendation.get('must_fix') else ""}
            {f'''
            <div class="rec-items">
                <strong>Should Fix:</strong>
                <ul>
                    {"".join([f"<li>{escape_html(item)}</li>" for item in recommendation.get('should_fix', [])])}
                </ul>
            </div>
            ''' if recommendation.get('should_fix') else ""}
        </div>
    </div>

    <!-- CODE REVIEW - ISSUES BY FILE -->
    <div class="section">
        <h2>🔍 Code Review — Issues by File</h2>
        {f'''<div class="no-issues">✅ No issues detected</div>''' if not findings else f'''
        <div class="files-container">
            {"".join([f'''
            <div class="file-item">
                <div class="file-header" onclick="toggleFile(this)">
                    <span class="file-path">{escape_html(file_path)}</span>
                    <span class="file-count">{len(issues)} issue{"s" if len(issues) != 1 else ""}</span>
                    <span class="file-toggle">▶</span>
                </div>
                <div class="file-content">
                    {"".join([f'''
                    <div class="finding {issue.get('severity', 'low').lower()}">
                        <div class="finding-title">
                            <span>{escape_html(issue.get('title', 'Issue'))}</span>
                            <span class="severity-badge {issue.get('severity', 'LOW').lower()}">{issue.get('severity', 'LOW')}</span>
                        </div>
                        {f"<div class='finding-detail'><strong>Line:</strong> {issue.get('line', 'N/A')}</div>" if issue.get('line') else ""}
                        <div class="finding-detail"><strong>Type:</strong> {escape_html(issue.get('type', 'Unknown'))}</div>
                        <div class="finding-detail"><strong>Description:</strong> {escape_html(issue.get('description', 'No description'))}</div>
                        {f"<div class='finding-detail'><strong>Impact:</strong> {escape_html(issue.get('impact', ''))}</div>" if issue.get('impact') else ""}
                        {f"<div class='finding-detail'><strong>Code:</strong> <pre><code>{escape_html(issue.get('code', ''))}</code></pre></div>" if issue.get('code') else ""}
                        {f"<div class='finding-detail'><strong>Recommended Fix:</strong> <pre><code>{escape_html(issue.get('fix') or issue.get('suggestion', ''))}</code></pre></div>" if (issue.get('fix') or issue.get('suggestion')) else ""}
                    </div>
                    ''' for issue in sorted(issues, key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x.get('severity', 'LOW'), 4))])}
                </div>
            </div>
            ''' for file_path, issues in sorted(findings_by_file.items())])}
        </div>
        '''}
    </div>

    {f'''
    <!-- SPRING BOOT VALIDATION -->
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
            ''' for category, details in [
                ("Architecture", spring_boot.get('architecture', {{}})),
                ("Security", spring_boot.get('security', {{}})),
                ("Performance", spring_boot.get('performance', {{}})),
                ("Transactions", spring_boot.get('transactions', {{}}))
            ] for score in [details.get('score', 0)]])}
        </table>
    </div>
    ''' if spring_boot else ""}

    {f'''
    <!-- TEST COVERAGE -->
    <div class="section">
        <h2>📈 Test Coverage</h2>
        <table class="validation-table">
            <tr>
                <td>Overall Coverage</td>
                <td><strong>{test_coverage.get('overall', 'N/A')}</strong></td>
            </tr>
            <tr>
                <td>Unit Tests</td>
                <td>{test_coverage.get('by_type', {{}}).get('unit', 'N/A')}</td>
            </tr>
            <tr>
                <td>Integration Tests</td>
                <td>{test_coverage.get('by_type', {{}}).get('integration', 'N/A')}</td>
            </tr>
        </table>
    </div>
    ''' if test_coverage else ""}

    {f'''
    <!-- API CHANGES -->
    <div class="section">
        <h2>🔗 API Changes</h2>
        <p><strong>Total Changes:</strong> {len(api_changes)}</p>
        <p><strong>Breaking Changes:</strong> {len([c for c in api_changes if c.get('type') == 'BREAKING'])}</p>
        {f"<p><strong>Non-Breaking Changes:</strong> {len([c for c in api_changes if c.get('type') == 'NON_BREAKING'])}</p>" if [c for c in api_changes if c.get('type') == 'NON_BREAKING'] else ""}
        {f"<p><strong>New Endpoints:</strong> {len([c for c in api_changes if c.get('type') == 'NEW'])}</p>" if [c for c in api_changes if c.get('type') == 'NEW'] else ""}
    </div>
    ''' if api_changes else ""}

    {f'''
    <!-- IMPACT ANALYSIS -->
    <div class="section">
        <h2>📊 Impact Analysis (Step 5)</h2>

        {f'''
        <h3>Risk Assessment</h3>
        <p><strong>Overall Risk Level:</strong>
            <span style="color: {{"HIGH": "#d32f2f", "MEDIUM": "#ff6f00", "LOW": "#388e3c"}.get(impact_analysis.get("impact_summary", {{}}).get("risk_level", "UNKNOWN"), "#333")}; font-weight: bold;">
                {impact_analysis.get("impact_summary", {{}}).get("risk_level", "UNKNOWN")}
            </span>
        </p>
        ''' if impact_analysis.get("impact_summary") else ""}

        {f'''
        <h3>Impact Breakdown</h3>
        <ul>
            <li><strong>Direct Impact:</strong> {impact_analysis.get("impact_summary", {{}}).get("direct_impact", "N/A")} files directly changed</li>
            <li><strong>Transitive Impact:</strong> {impact_analysis.get("impact_summary", {{}}).get("transitive_impact", "N/A")} files affected (cascading)</li>
            <li><strong>Total Affected:</strong> {impact_analysis.get("impact_summary", {{}}).get("total_affected_files", "N/A")} files total</li>
        </ul>
        ''' if impact_analysis.get("impact_summary") else ""}

        {f'''
        <h3>Impact by Layer</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;"><strong>Layer</strong></th>
                    <th style="text-align: center; padding: 8px; border: 1px solid #ddd;"><strong>Files Affected</strong></th>
                </tr>
            </thead>
            <tbody>
                {f"".join([f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{layer}</td><td style="text-align: center; padding: 8px; border: 1px solid #ddd;">{count}</td></tr>' for layer, count in impact_analysis.get("impact_by_layer", {{}}).items() if count > 0])}
            </tbody>
        </table>
        ''' if impact_analysis.get("impact_by_layer") else ""}

        {f'''
        <h3>Critical Call Paths Affected</h3>
        <ul>
            {f"".join([f'<li><strong>{" → ".join(path.get("path", []))}</strong> [<span style="color: {{"HIGH": "#d32f2f", "MEDIUM": "#ff6f00", "LOW": "#388e3c"}.get(path.get("risk", "UNKNOWN"), "#333")}">{path.get("risk", "UNKNOWN")}</span>]<br/><em>{escape_html(path.get("description", ""))}</em></li>' for path in impact_analysis.get("critical_paths", [])[:3]])}
        </ul>
        ''' if impact_analysis.get("critical_paths") else ""}

        {f"<p><strong>Affected APIs:</strong> {', '.join([a.get('endpoint', a) for a in impact_analysis.get('affected_apis', [])])}</p>" if impact_analysis.get("affected_apis") else ""}
    </div>
    ''' if impact_analysis else ""}

    {f'''
    <!-- POSITIVE OBSERVATIONS -->
    <div class="section">
        <h2>✨ Positive Observations</h2>
        {f"<p><strong>Strengths:</strong></p><ul>{''.join([f'<li>{escape_html(s)}</li>' for s in positive_obs.get('strengths', [])])}</ul>" if positive_obs.get("strengths") else ""}
        {f"<p><strong>Best Practices Followed:</strong></p><ul>{''.join([f'<li>{escape_html(p)}</li>' for p in positive_obs.get('best_practices', [])])}</ul>" if positive_obs.get("best_practices") else ""}
        {f"<p><strong>Good Patterns Used:</strong></p><ul>{''.join([f'<li>{escape_html(p)}</li>' for p in positive_obs.get('good_patterns', [])])}</ul>" if positive_obs.get("good_patterns") else ""}
    </div>
    ''' if positive_obs else ""}

    {f'''
    <!-- AI SUMMARY -->
    <div class="section">
        <h2>🤖 AI Summary</h2>
        {f"<p>{escape_html(ai_summary.get('overall_summary', ''))}</p>" if ai_summary.get("overall_summary") else ""}
        {f"<p><strong>Key Takeaways:</strong></p><ul>{''.join([f'<li>{escape_html(t)}</li>' for t in ai_summary.get('key_takeaways', [])])}</ul>" if ai_summary.get("key_takeaways") else ""}
    </div>
    ''' if ai_summary else ""}

</div>

<div class="footer">
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Automated Code Review
</div>
</body>
</html>
"""
    return html


def save_simple_html_report(data, output_file=None, auto_open=True):
    """Save HTML report to file and optionally open in browser

    Guaranteed valid HTML output even if generation fails.

    Args:
        data: Analysis data dictionary
        output_file: Optional output path
        auto_open: Whether to auto-open in browser (default: True)

    Returns:
        output_file path if successful, None otherwise
    """
    pr_number = data.get('metadata', {}).get('pr_number', 'unknown')

    # Try to generate main HTML
    try:
        html = generate_simple_html_report(data)
        is_valid, error_msg = validate_html(html)

        if not is_valid:
            print(f"⚠️ Generated HTML validation failed: {error_msg}")
            print(f"   Falling back to minimal report")
            html = generate_fallback_html(pr_number, f"HTML validation failed: {error_msg}")
    except Exception as e:
        print(f"⚠️ Error generating HTML: {e}")
        print(f"   Generating fallback report")
        html = generate_fallback_html(pr_number, str(e))

    # Determine output file
    if not output_file:
        try:
            output_file = f".ai-review/pr-{pr_number}-data.html"
        except Exception:
            output_file = ".ai-review/pr-unknown-data.html"

    # Save HTML (guaranteed valid at this point)
    try:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML report generated: {output_file}")

        # Auto-open in browser if requested
        if auto_open:
            open_html_in_browser(output_file)

        return output_file
    except Exception as e:
        print(f"❌ Error saving HTML report: {e}")
        # Even if file save fails, the analysis is complete
        return None


if __name__ == '__main__':
    try:
        # Read JSON from stdin (no file needed)
        data = json.load(sys.stdin)

        # Generate and save HTML report (auto-open disabled in subprocess)
        save_simple_html_report(data, auto_open=False)

        sys.exit(0)
    except (json.JSONDecodeError, EOFError) as e:
        print(f"❌ Error reading JSON from stdin: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
PR Code Review - Token-Free HTML Report Generator
Generates rich HTML reports with ZERO LLM tokens usage
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

def basename_filter(path):
    """Extract basename from file path"""
    return os.path.basename(path)

def load_html_template():
    """Load external HTML template using Jinja2"""
    template_dir = Path(__file__).parent
    
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    # Add custom filters
    env.filters['basename'] = basename_filter
    
    # Load template
    template = env.get_template('pr-review-template.html')
    return template

def generate_html_report(data_file):
    """Main function to generate complete HTML report"""
    
    # Load review data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Load template
    template = load_html_template()
    
    # Render with data
    html = template.render(
        metadata=data.get('metadata', {}),
        summary=data.get('summary', {}),
        findings=data.get('findings', []),
        files_reviewed=data.get('files_reviewed', []),
        files_excluded=data.get('files_excluded', []),
        impact_analysis=data.get('impact_analysis', {}),
        spring_boot_validation=data.get('spring_boot_validation', {}),
        api_changes=data.get('api_changes', []),
        test_coverage=data.get('test_coverage', {}),
        positive_observations=data.get('positive_observations', []),
        overall_recommendation=data.get('overall_recommendation', {}),
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # Save HTML report
    pr_number = data.get('metadata', {}).get('pr_number', 'unknown')
    output = f".ai-review/pr-{pr_number}-review.html"
    
    # Ensure directory exists
    os.makedirs('.ai-review', exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML Report Generated: {output}")
    print(f"📊 Files Reviewed: {len(data.get('files_reviewed', []))}")
    print(f"📄 Issues Found: {len(data.get('findings', []))}")
    print(f"🎯 Test Coverage: {data.get('test_coverage', {}).get('overall', 'N/A')}")
    print(f"\n💡 Open in browser: {os.path.abspath(output)}")
    
    return output

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_pr_report.py <review-data.json>")
        print("\nExample:")
        print("  python generate_pr_report.py .ai-review/pr-<number>-data.json")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    if not os.path.exists(data_file):
        print(f"❌ Error: File not found: {data_file}")
        sys.exit(1)
    
    try:
        generate_html_report(data_file)
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PR #{pr_number} - Code Review Report</title>
        
        <!-- External CDN Resources - Zero tokens -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        
        <!-- Embedded Styles - Loaded from external file -->
        <style>
            {custom_styles}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Header Section -->
            {header_html}
            
            <!-- Summary Dashboard -->
            {summary_dashboard_html}
            
            <!-- Critical Findings -->
            {critical_findings_html}
            
            <!-- Spring Boot Validation -->
            {spring_validation_html}
            
            <!-- API Impact Analysis -->
            {api_impact_html}
            
            <!-- Test Coverage -->
            {test_coverage_html}
            
            <!-- Dependency Graph -->
            {dependency_graph_html}
            
            <!-- File-by-File Review -->
            {file_reviews_html}
            
            <!-- Recommendations -->
            {recommendations_html}
        </div>
        
        <!-- External Libraries - Zero tokens -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
        
        <script>
            {interactive_scripts}
        </script>
    </body>
    </html>
    """

def generate_header_html(metadata):
    """Generate header section"""
    return f"""
    <header class="review-header">
        <div class="row align-items-center mb-4">
            <div class="col-md-8">
                <h1 class="display-4">
                    <i class="fas fa-code-branch"></i> PR #{metadata['pr_number']}
                </h1>
                <h2 class="text-muted">{metadata['title']}</h2>
                <div class="meta-info mt-3">
                    <span class="badge bg-primary">
                        <i class="fas fa-user"></i> {metadata['author']}
                    </span>
                    <span class="badge bg-info">
                        {metadata['branch']}
                    </span>
                    <span class="badge bg-secondary">
                        <i class="fas fa-calendar"></i> {metadata['review_date']}
                    </span>
                    {generate_jira_badges(metadata.get('jira_tickets', []))}
                </div>
            </div>
            <div class="col-md-4 text-end">
                <button class="btn btn-success" onclick="window.print()">
                    <i class="fas fa-print"></i> Print Report
                </button>
                <button class="btn btn-primary" onclick="exportToPDF()">
                    <i class="fas fa-file-pdf"></i> Export PDF
                </button>
            </div>
        </div>
    </header>
    """

def generate_jira_badges(tickets):
    """Generate JIRA ticket badges"""
    if not tickets:
        return ""
    return " ".join([
        f'<span class="badge bg-warning text-dark">'
        f'<i class="fas fa-ticket-alt"></i> {ticket}'
        f'</span>'
        for ticket in tickets
    ])

def generate_summary_dashboard(summary):
    """Generate summary dashboard with metrics"""
    severity_colors = {
        'critical': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'secondary'
    }
    
    return f"""
    <section class="summary-dashboard card shadow-lg mb-4">
        <div class="card-header bg-gradient-primary text-white">
            <h3><i class="fas fa-chart-line"></i> Review Summary</h3>
        </div>
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value">{summary['files_changed']}</div>
                        <div class="metric-label">Files Changed</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value text-success">+{summary['lines_added']}</div>
                        <div class="metric-value text-danger">-{summary['lines_deleted']}</div>
                        <div class="metric-label">Lines Changed</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value text-danger">{summary['critical_issues']}</div>
                        <div class="metric-label">Critical Issues</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value text-warning">{summary['high_issues']}</div>
                        <div class="metric-label">High Priority</div>
                    </div>
                </div>
            </div>
            
            <!-- Test Coverage Progress Bar -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <h5>Test Coverage: {summary['test_coverage']}</h5>
                    <div class="progress" style="height: 30px;">
                        <div class="progress-bar bg-success" 
                             role="progressbar" 
                             style="width: {summary['test_coverage']}"
                             aria-valuenow="{summary['test_coverage'][:-1]}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            {summary['test_coverage']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """

def generate_findings_table(findings):
    """Generate interactive findings table with filtering"""
    if not findings:
        return '<div class="alert alert-success">✅ No issues found!</div>'
    
    severity_icons = {
        'CRITICAL': 'fas fa-times-circle text-danger',
        'HIGH': 'fas fa-exclamation-triangle text-warning',
        'MEDIUM': 'fas fa-info-circle text-info',
        'LOW': 'fas fa-check-circle text-secondary'
    }
    
    # Filter buttons
    html = """
    <div class="findings-filters mb-3">
        <button class="btn btn-sm btn-outline-secondary" onclick="filterFindings('ALL')">All</button>
        <button class="btn btn-sm btn-outline-danger" onclick="filterFindings('CRITICAL')">Critical</button>
        <button class="btn btn-sm btn-outline-warning" onclick="filterFindings('HIGH')">High</button>
        <button class="btn btn-sm btn-outline-info" onclick="filterFindings('MEDIUM')">Medium</button>
        <button class="btn btn-sm btn-outline-secondary" onclick="filterFindings('LOW')">Low</button>
    </div>
    """
    
    # Findings table
    html += """
    <table class="table table-hover findings-table">
        <thead class="table-dark">
            <tr>
                <th width="10%">Severity</th>
                <th width="15%">Category</th>
                <th width="20%">File</th>
                <th width="35%">Issue</th>
                <th width="20%">Action</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for finding in findings:
        icon = severity_icons.get(finding['severity'], 'fas fa-circle')
        html += f"""
        <tr class="finding-row" data-severity="{finding['severity']}">
            <td>
                <span class="severity-badge badge bg-{finding['severity'].lower()}">
                    <i class="{icon}"></i> {finding['severity']}
                </span>
            </td>
            <td><span class="badge bg-secondary">{finding['category']}</span></td>
            <td>
                <code>{finding['file']}</code>
                <small class="text-muted d-block">Line {finding['line']}</small>
            </td>
            <td>
                <strong>{finding['title']}</strong>
                <p class="mb-0 text-muted small">{finding['description']}</p>
                <details class="mt-2">
                    <summary class="text-primary" style="cursor: pointer;">
                        View Code & Suggestion
                    </summary>
                    <pre class="bg-light p-2 mt-2"><code>{finding.get('code_snippet', 'N/A')}</code></pre>
                    <div class="alert alert-info mt-2">
                        <strong>Suggestion:</strong> {finding['suggestion']}
                    </div>
                </details>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" 
                        onclick="copyToClipboard('{finding['id']}')">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </td>
        </tr>
        """
    
    html += """
        </tbody>
    </table>
    """
    
    return html

def generate_spring_validation_dashboard(validation):
    """Generate Spring Boot validation dashboard with charts"""
    return f"""
    <section class="spring-validation card shadow mb-4">
        <div class="card-header bg-success text-white">
            <h3><i class="fas fa-leaf"></i> Spring Boot Best Practices Validation</h3>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <canvas id="springScoresChart"></canvas>
                </div>
                <div class="col-md-6">
                    <div class="validation-details">
                        <h5>Architecture (Score: {validation['architecture']['score']}/10)</h5>
                        <ul>
                            {"".join([f"<li>{issue}</li>" for issue in validation['architecture']['issues']])}
                        </ul>
                        
                        <h5>Security (Score: {validation['security']['score']}/10)</h5>
                        <ul>
                            {"".join([f"<li>{issue}</li>" for issue in validation['security']['issues']])}
                        </ul>
                        
                        <h5>Performance (Score: {validation['performance']['score']}/10)</h5>
                        <ul>
                            {"".join([f"<li>{issue}</li>" for issue in validation['performance']['issues']])}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <script>
        // Chart.js visualization
        const ctx = document.getElementById('springScoresChart').getContext('2d');
        new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: ['Architecture', 'Security', 'Performance', 'Transactions', 'Error Handling'],
                datasets: [{{
                    label: 'Score',
                    data: [
                        {validation['architecture']['score']},
                        {validation['security']['score']},
                        {validation['performance']['score']},
                        8.5, 7.0
                    ],
                    backgroundColor: 'rgba(40, 167, 69, 0.2)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 10
                    }}
                }}
            }}
        }});
    </script>
    """

def generate_api_impact_section(api_changes):
    """Generate API impact analysis section"""
    if not api_changes:
        return '<div class="alert alert-success">✅ No API changes detected</div>'
    
    html = """
    <section class="api-impact card shadow mb-4">
        <div class="card-header bg-info text-white">
            <h3><i class="fas fa-exchange-alt"></i> API Impact Analysis</h3>
        </div>
        <div class="card-body">
    """
    
    for change in api_changes:
        breaking_badge = 'danger' if change['type'] == 'BREAKING' else 'warning'
        html += f"""
        <div class="api-change-card alert alert-{breaking_badge}">
            <div class="row">
                <div class="col-md-8">
                    <h5>
                        <span class="badge bg-{breaking_badge}">{change['type']}</span>
                        <code>{change['endpoint']}</code>
                    </h5>
                    <p><strong>Change:</strong> {change['change']}</p>
                    <p><strong>Impact Level:</strong> {change['impact']}</p>
                    <p><strong>Backward Compatible:</strong> {'✅ Yes' if change['backward_compatible'] else '❌ No'}</p>
                </div>
                <div class="col-md-4">
                    <h6>Affected Consumers:</h6>
                    <ul>
                        {"".join([f"<li><code>{consumer}</code></li>" for consumer in change['affected_consumers']])}
                    </ul>
                    <small class="text-muted">{change.get('migration_notes', '')}</small>
                </div>
            </div>
        </div>
        """
    
    html += """
        </div>
    </section>
    """
    return html

def generate_dependency_graph(graph_data):
    """Generate interactive dependency graph using Cytoscape.js"""
    return f"""
    <section class="dependency-graph card shadow mb-4">
        <div class="card-header bg-dark text-white">
            <h3><i class="fas fa-project-diagram"></i> Dependency & Impact Graph</h3>
        </div>
        <div class="card-body">
            <div id="cy" style="width: 100%; height: 600px; border: 1px solid #ddd;"></div>
        </div>
    </section>
    
    <script>
        // Cytoscape.js dependency graph
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {json.dumps(graph_data)},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': '#666',
                        'label': 'data(id)',
                        'text-valign': 'center',
                        'color': '#fff',
                        'text-outline-width': 2,
                        'text-outline-color': '#666'
                    }}
                }},
                {{
                    selector: 'node[changes="modified"]',
                    style: {{
                        'background-color': '#ff6b6b'
                    }}
                }},
                {{
                    selector: 'node[type="controller"]',
                    style: {{
                        'shape': 'rectangle'
                    }}
                }},
                {{
                    selector: 'node[type="service"]',
                    style: {{
                        'shape': 'ellipse'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                animate: true,
                animationDuration: 1000
            }}
        }});
    </script>
    """

def generate_test_coverage_section(coverage):
    """Generate test coverage visualization"""
    return f"""
    <section class="test-coverage card shadow mb-4">
        <div class="card-header bg-primary text-white">
            <h3><i class="fas fa-vial"></i> Test Coverage Analysis</h3>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <canvas id="coverageChart"></canvas>
                </div>
                <div class="col-md-6">
                    <h5>Coverage by Type</h5>
                    <div class="coverage-breakdown">
                        <div class="mb-3">
                            <label>Unit Tests: {coverage['by_type']['unit']}</label>
                            <div class="progress">
                                <div class="progress-bar bg-success" style="width: {coverage['by_type']['unit']}"></div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label>Integration: {coverage['by_type']['integration']}</label>
                            <div class="progress">
                                <div class="progress-bar bg-warning" style="width: {coverage['by_type']['integration']}"></div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label>E2E: {coverage['by_type']['e2e']}</label>
                            <div class="progress">
                                <div class="progress-bar bg-danger" style="width: {coverage['by_type']['e2e']}"></div>
                            </div>
                        </div>
                    </div>
                    
                    <h5 class="mt-4">Coverage Gaps</h5>
                    <ul class="list-group">
                        {"".join([
                            f'<li class="list-group-item">'
                            f'<code>{gap["file"]}</code><br>'
                            f'<small>Methods: {", ".join(gap["methods"])}</small><br>'
                            f'<small class="text-muted">{gap["reason"]}</small>'
                            f'</li>'
                            for gap in coverage['gaps']
                        ])}
                    </ul>
                </div>
            </div>
        </div>
    </section>
    
    <script>
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Unit', 'Integration', 'E2E', 'Uncovered'],
                datasets: [{{
                    data: [
                        {coverage['by_type']['unit'][:-1]},
                        {coverage['by_type']['integration'][:-1]},
                        {coverage['by_type']['e2e'][:-1]},
                        {100 - int(coverage['overall'][:-1])}
                    ],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#6c757d']
                }}]
            }}
        }});
    </script>
    """

def generate_file_reviews_section(file_reviews):
    """Generate file-by-file review section"""
    html = """
    <section class="file-reviews card shadow mb-4">
        <div class="card-header bg-secondary text-white">
            <h3><i class="fas fa-file-code"></i> File-by-File Review</h3>
        </div>
        <div class="card-body">
    """
    
    for file in file_reviews:
        validation_icons = {
            'PASS': '<i class="fas fa-check-circle text-success"></i>',
            'FAIL': '<i class="fas fa-times-circle text-danger"></i>',
            'PARTIAL': '<i class="fas fa-exclamation-circle text-warning"></i>'
        }
        
        html += f"""
        <div class="file-review-card card mb-3">
            <div class="card-header">
                <h5>
                    <i class="fas fa-file-alt"></i> 
                    <code>{file['path']}</code>
                    <span class="badge bg-primary float-end">
                        +{file['additions']} / -{file['deletions']}
                    </span>
                </h5>
            </div>
            <div class="card-body">
                <p><strong>AI Description:</strong> {file['description']}</p>
                
                <div class="row mt-3">
                    <div class="col-md-3">
                        <strong>Code Quality:</strong><br>
                        {validation_icons[file['validation']['code_quality']]} 
                        {file['validation']['code_quality']}
                    </div>
                    <div class="col-md-3">
                        <strong>Spring Boot:</strong><br>
                        {validation_icons[file['validation']['spring_boot_compliance']]} 
                        {file['validation']['spring_boot_compliance']}
                    </div>
                    <div class="col-md-3">
                        <strong>Test Coverage:</strong><br>
                        {validation_icons[file['validation']['test_coverage']]} 
                        {file['validation']['test_coverage']}
                    </div>
                    <div class="col-md-3">
                        <strong>Security:</strong><br>
                        {validation_icons[file['validation']['security']]} 
                        {file['validation']['security']}
                    </div>
                </div>
                
                {f'<div class="alert alert-warning mt-3"><strong>Issues:</strong> {", ".join(file["issues"])}</div>' if file.get('issues') else ''}
            </div>
        </div>
        """
    
    html += """
        </div>
    </section>
    """
    return html

def generate_recommendations_section(positive, recommendations):
    """Generate recommendations and positive observations"""
    return f"""
    <section class="recommendations card shadow mb-4">
        <div class="card-header bg-success text-white">
            <h3><i class="fas fa-thumbs-up"></i> Positive Observations</h3>
        </div>
        <div class="card-body">
            <ul class="list-group">
                {"".join([f'<li class="list-group-item"><i class="fas fa-check text-success"></i> {obs}</li>' for obs in positive])}
            </ul>
        </div>
    </section>
    
    <section class="recommendations card shadow mb-4">
        <div class="card-header bg-warning text-dark">
            <h3><i class="fas fa-lightbulb"></i> Recommendations</h3>
        </div>
        <div class="card-body">
            <ol class="list-group list-group-numbered">
                {"".join([f'<li class="list-group-item">{rec}</li>' for rec in recommendations])}
            </ol>
        </div>
    </section>
    """

def generate_interactive_scripts():
    """Generate interactive JavaScript functions"""
    return """
    // Filter findings by severity
    function filterFindings(severity) {
        const rows = document.querySelectorAll('.finding-row');
        rows.forEach(row => {
            if (severity === 'ALL' || row.dataset.severity === severity) {
                row.style.display = 'table-row';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    // Copy finding ID to clipboard
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            alert('Finding ID copied to clipboard!');
        });
    }
    
    // Export to PDF
    function exportToPDF() {
        window.print();
    }
    
    // Initialize on load
    document.addEventListener('DOMContentLoaded', function() {
        console.log('PR Review Report Loaded');
    });
    """

def generate_custom_styles():
    """Generate custom CSS styles"""
    return """
    /* Custom Styles */
    .review-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #495057;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .severity-badge {
        font-size: 0.85rem;
        padding: 0.4rem 0.8rem;
    }
    
    .finding-row {
        transition: background-color 0.2s;
    }
    
    .finding-row:hover {
        background-color: #f8f9fa;
    }
    
    .api-change-card {
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .file-review-card {
        border-left: 3px solid #007bff;
    }
    
    @media print {
        .btn { display: none; }
        .findings-filters { display: none; }
    }
    """

def generate_html_report(data_file):
    """Main function to generate complete HTML report"""
    
    # Load review data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Generate all HTML sections
    header = generate_header_html(data['metadata'])
    summary = generate_summary_dashboard(data['summary'])
    findings = generate_findings_table(data['findings'])
    spring_validation = generate_spring_validation_dashboard(data['spring_boot_validation'])
    api_impact = generate_api_impact_section(data['api_changes'])
    test_coverage = generate_test_coverage_section(data['test_coverage'])
    dependency_graph = generate_dependency_graph(data['dependency_graph'])
    file_reviews = generate_file_reviews_section(data['file_reviews'])
    recommendations = generate_recommendations_section(
        data['positive_observations'],
        data['recommendations']
    )
    
    # Assemble complete HTML
    full_html = load_html_template().format(
        pr_number=data['metadata']['pr_number'],
        custom_styles=generate_custom_styles(),
        header_html=header,
        summary_dashboard_html=summary,
        critical_findings_html=findings,
        spring_validation_html=spring_validation,
        api_impact_html=api_impact,
        test_coverage_html=test_coverage,
        dependency_graph_html=dependency_graph,
        file_reviews_html=file_reviews,
        recommendations_html=recommendations,
        interactive_scripts=generate_interactive_scripts()
    )
    
    # Save HTML report
    output_file = f".ai-review/pr-{data['metadata']['pr_number']}-review.html"
    os.makedirs('.ai-review', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ HTML Report Generated: {output_file}")
    print(f"📊 Findings: {len(data['findings'])} total")
    print(f"📄 Files Reviewed: {len(data['file_reviews'])}")
    print(f"🎯 Test Coverage: {data['test_coverage']['overall']}")
    
    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_pr_report.py <data.json>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    generate_html_report(data_file)

#!/usr/bin/env python3
"""
JIRA Comment Formatter for PR Code Review
Generates Markdown-formatted comments for JIRA integration
"""

import json
import sys
from datetime import datetime

def format_jira_comment(data):
    """
    Format review data as JIRA-compatible Markdown comment
    """
    
    metadata = data['metadata']
    summary = data['summary']
    findings = data['findings']
    spring_validation = data['spring_boot_validation']
    test_coverage = data['test_coverage']
    api_changes = data['api_changes']
    recommendations = data['recommendations']
    
    # Build comment sections
    comment = []
    
    # Header
    comment.append(f"🤖 *Automated PR Review - PR #{metadata['pr_number']}*")
    comment.append("")
    comment.append("----")
    comment.append("")
    comment.append(f"*Branch:* {{{{monospace}}}}{metadata['branch']}{{{{monospace}}}}")
    comment.append(f"*Author:* {metadata['author']}")
    comment.append(f"*Review Date:* {metadata['review_date']}")
    comment.append("")
    comment.append("----")
    comment.append("")
    
    # Summary Table
    comment.append("h3. 📊 Summary")
    comment.append("")
    comment.append("|| Metric || Value ||")
    comment.append(f"| Files Changed | {summary['files_changed']} |")
    comment.append(f"| Lines Added/Deleted | {{color:green}}+{summary['lines_added']}{{color}} / {{color:red}}-{summary['lines_deleted']}{{color}} |")
    comment.append(f"| Critical Issues | {{color:red}}⚠️ {summary['critical_issues']}{{color}} |")
    comment.append(f"| High Priority | {{color:orange}}🟠 {summary['high_issues']}{{color}} |")
    comment.append(f"| Test Coverage | {summary['test_coverage']} |")
    comment.append("")
    comment.append("----")
    comment.append("")
    
    # Critical Issues
    critical_findings = [f for f in findings if f['severity'] in ['CRITICAL', 'HIGH']]
    
    if critical_findings:
        comment.append(f"h3. 🔴 Critical & High Priority Issues ({len(critical_findings)})")
        comment.append("")
        
        for finding in critical_findings[:5]:  # Show top 5
            severity_color = 'red' if finding['severity'] == 'CRITICAL' else 'orange'
            
            comment.append(f"h4. {finding['id']}: {finding['title']}")
            comment.append(f"*Severity:* {{color:{severity_color}}}{finding['severity']}{{color}}")
            comment.append(f"*File:* {{{{monospace}}}}{finding['file']}:{finding['line']}{{{{monospace}}}}")
            comment.append(f"*Impact:* {finding['impact']}")
            comment.append(f"*Suggested Fix:* {finding['suggestion']}")
            comment.append("")
        
        if len(critical_findings) > 5:
            comment.append(f"_{len(critical_findings) - 5} more issues in full report_")
            comment.append("")
    else:
        comment.append("h3. ✅ No Critical or High Priority Issues")
        comment.append("")
    
    comment.append("----")
    comment.append("")
    
    # Spring Boot Validation
    comment.append("h3. 🎯 Spring Boot Validation")
    comment.append("")
    comment.append("|| Category || Score || Status ||")
    
    for category_key, category_name in [
        ('architecture', 'Architecture'),
        ('security', 'Security'),
        ('performance', 'Performance'),
        ('transactions', 'Transactions')
    ]:
        score = spring_validation.get(category_key, {}).get('score', 0)
        
        if score >= 8.0:
            status = "{{color:green}}✅ PASS{{color}}"
        elif score >= 6.0:
            status = "{{color:orange}}⚠️ WARNING{{color}}"
        else:
            status = "{{color:red}}❌ FAIL{{color}}"
        
        comment.append(f"| {category_name} | {score}/10 | {status} |")
        
        # Show issues for failing categories
        issues = spring_validation.get(category_key, {}).get('issues', [])
        if issues and score < 8.0:
            for issue in issues[:2]:  # Show top 2 issues per category
                comment.append(f"| | {{color:gray}}• {issue}{{color}} | |")
    
    comment.append("")
    comment.append("----")
    comment.append("")
    
    # Test Coverage
    comment.append("h3. 📈 Test Coverage")
    comment.append("")
    comment.append(f"*Overall Coverage:* {test_coverage['overall']}")
    comment.append("")
    comment.append("|| Test Type || Coverage ||")
    comment.append(f"| Unit Tests | {test_coverage['by_type']['unit']} |")
    comment.append(f"| Integration Tests | {test_coverage['by_type']['integration']} |")
    comment.append(f"| E2E Tests | {test_coverage['by_type']['e2e']} |")
    comment.append("")
    
    if test_coverage.get('gaps'):
        comment.append(f"*Coverage Gaps:* {len(test_coverage['gaps'])} methods missing tests")
        for gap in test_coverage['gaps'][:3]:
            comment.append(f"* {{{{monospace}}}}{gap['file']}{{{{monospace}}}} - {', '.join(gap['methods'])}")
        comment.append("")
    
    comment.append("----")
    comment.append("")
    
    # API Changes
    if api_changes:
        breaking_changes = [c for c in api_changes if c['type'] == 'BREAKING']
        
        if breaking_changes:
            comment.append("h3. 🔗 API Breaking Changes")
            comment.append("")
            comment.append("{warning}Breaking changes detected that will affect API consumers{warning}")
            comment.append("")
            
            for change in breaking_changes:
                comment.append(f"h4. {{{{monospace}}}}{change['endpoint']}{{{{monospace}}}}")
                comment.append(f"*Change:* {change['change']}")
                comment.append(f"*Impact Level:* {{color:red}}{change['impact']}{{color}}")
                comment.append(f"*Backward Compatible:* {'✅ Yes' if change['backward_compatible'] else '❌ No'}")
                
                if change.get('affected_consumers'):
                    comment.append(f"*Affected Consumers:*")
                    for consumer in change['affected_consumers']:
                        comment.append(f"* {{{{monospace}}}}{consumer}{{{{monospace}}}}")
                
                if change.get('migration_notes'):
                    comment.append(f"*Migration Notes:* {change['migration_notes']}")
                
                comment.append("")
            
            comment.append("----")
            comment.append("")
    
    # Recommendations
    comment.append("h3. ✅ Recommendation")
    comment.append("")
    
    overall_rec_raw = data.get('overall_recommendation', 'APPROVE')
    if isinstance(overall_rec_raw, dict):
        overall_rec = overall_rec_raw.get('decision', 'APPROVE')
        rec_reason = overall_rec_raw.get('reason', '')
        must_fix = overall_rec_raw.get('must_fix', [])
        should_fix = overall_rec_raw.get('should_fix', [])
    else:
        overall_rec = overall_rec_raw
        rec_reason = data.get('overall_recommendation_reason', '')
        must_fix = []
        should_fix = []
    
    if overall_rec == 'APPROVE':
        comment.append("{panel:bgColor=#e3fcef}✅ *APPROVE* - Changes are ready to merge{panel}")
    elif overall_rec == 'REQUEST_CHANGES':
        comment.append("{panel:bgColor=#ffebe9}⚠️ *REQUEST CHANGES* - Critical issues must be addressed{panel}")
    else:
        comment.append("{panel:bgColor=#fff4e6}⚠️ *APPROVE WITH COMMENTS* - Consider addressing feedback{panel}")
    
    if rec_reason:
        comment.append("")
        comment.append(f"_{rec_reason}_")
    
    comment.append("")
    
    # Must-fix items (from dict or from recommendations list)
    if must_fix:
        comment.append("*Must Fix Before Merge:*")
        for i, item in enumerate(must_fix, 1):
            comment.append(f"# {item}")
        comment.append("")
    else:
        critical_recs = [r for r in recommendations if '🔴 CRITICAL' in r or '🟠 HIGH' in r]
        if critical_recs:
            comment.append("*Must Fix Before Merge:*")
            for i, rec in enumerate(critical_recs, 1):
                clean_rec = rec.replace('🔴 CRITICAL:', '').replace('🟠 HIGH:', '').strip()
                comment.append(f"# {clean_rec}")
            comment.append("")
    
    # Should-fix / optional improvements
    if should_fix:
        comment.append("*Should Fix:*")
        for item in should_fix:
            comment.append(f"* {item}")
        comment.append("")
    else:
        optional_recs = [r for r in recommendations if '🟡 MEDIUM' in r or '🟢 LOW' in r]
        if optional_recs and len(optional_recs) <= 3:
            comment.append("*Optional Improvements:*")
            for rec in optional_recs:
                clean_rec = rec.replace('🟡 MEDIUM:', '').replace('🟢 LOW:', '').strip()
                comment.append(f"* {clean_rec}")
            comment.append("")
    
    comment.append("----")
    comment.append("")
    
    # Links to full reports
    comment.append("h3. 📄 Full Report")
    comment.append("")
    comment.append(f"[View Complete HTML Report|file://.ai-review/pr-{metadata['pr_number']}-review.html]")
    comment.append(f"[View JSON Data|file://.ai-review/pr-{metadata['pr_number']}-data.json]")
    comment.append("")
    comment.append("----")
    comment.append("")
    
    # Footer
    comment.append(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_")
    comment.append(f"_Review ID: {metadata.get('review_id', 'N/A')}_")
    comment.append(f"_Automated by PR Code Review Workflow_")
    
    return "\n".join(comment)

def generate_jira_comment_file(data_file, output_file=None):
    """Generate JIRA comment file from review data"""
    
    # Load review data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Format comment
    comment = format_jira_comment(data)
    
    # Determine output file
    if not output_file:
        pr_number = data['metadata']['pr_number']
        output_file = f".ai-review/pr-{pr_number}-jira-comment.txt"
    
    # Save comment
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(comment)
    
    print(f"✅ JIRA comment generated: {output_file}")
    print(f"📊 Comment length: {len(comment)} characters")
    print(f"🎫 Ready to post to JIRA tickets: {', '.join(data['metadata'].get('jira_tickets', []))}")
    
    return output_file

def format_compact_summary(data):
    """Generate compact one-line summary for notifications"""
    pr = data['metadata']['pr_number']
    critical = data['summary']['critical_issues']
    high = data['summary']['high_issues']
    rec_raw = data.get('overall_recommendation', 'APPROVE')
    rec = rec_raw.get('decision', 'APPROVE') if isinstance(rec_raw, dict) else rec_raw
    
    if rec == 'APPROVE':
        emoji = "✅"
    elif critical > 0:
        emoji = "🔴"
    else:
        emoji = "⚠️"
    
    return f"{emoji} PR#{pr}: {critical} critical, {high} high priority issues - {rec}"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python jira_formatter.py <review-data.json> [output.txt]")
        print("       python jira_formatter.py <review-data.json> --summary")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    if '--summary' in sys.argv:
        with open(data_file) as f:
            print(format_compact_summary(json.load(f)))
    else:
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        generate_jira_comment_file(data_file, output_file)

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
    Gracefully handles missing data to ensure comment is always generated.
    """

    # Extract data with safe defaults
    metadata = data.get('metadata', {})
    summary = data.get('summary', {})
    findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
    spring_validation = data.get('spring_boot_validation', {})
    test_coverage = data.get('test_coverage', {})
    api_changes = data.get('api_changes', []) if isinstance(data.get('api_changes'), list) else []
    recommendations = data.get('recommendations', []) if isinstance(data.get('recommendations'), list) else []
    impact_analysis = data.get('impact_analysis', {})
    
    # Build comment sections
    comment = []
    
    # Header
    comment.append(f"h1. Code Review - PR #{metadata.get('pr_number', 'unknown')}")
    comment.append("")
    comment.append(f"*Status:* {{color:blue}}{metadata.get('title', 'PR')}{{color}}")
    comment.append("")
    comment.append("|| Field || Value ||")
    comment.append(f"| PR Author | {metadata.get('author', 'Unknown')} |")
    comment.append(f"| Reviewer | {metadata.get('reviewer', 'Automated Review System')} |")
    comment.append(f"| Branch | {metadata.get('branch', 'N/A')} |")
    comment.append(f"| Review Date | {metadata.get('review_date', 'N/A')} |")
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

    # Add large PR note if pagination was used
    pagination = data.get('pagination_metadata', {})
    if pagination.get('pages_fetched', 1) > 1:
        comment.append("*Note:* Large PR analyzed across {} API pages ({} files total)".format(
            pagination['pages_fetched'],
            pagination['total_items_retrieved']
        ))
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
    
    # API Impact Analysis
    affected_apis = impact_analysis.get('affected_apis', []) if isinstance(impact_analysis.get('affected_apis'), list) else []
    if affected_apis:
        comment.append("h3. 🔗 Affected APIs")
        comment.append("")
        comment.append("|| API Endpoint || Method || Status ||")
        for api in affected_apis[:15]:  # Show top 15 APIs
            endpoint = api.get('path', api.get('endpoint', 'Unknown'))
            method = api.get('method', 'UNKNOWN')
            status = api.get('status', 'Modified')
            comment.append(f"| {{{{monospace}}}}{endpoint}{{{{monospace}}}} | {method} | {status} |")

        if len(affected_apis) > 15:
            comment.append(f"| ... and {len(affected_apis) - 15} more | | |")

        comment.append("")
        comment.append("----")
        comment.append("")

    # API Changes (Breaking/Non-Breaking)
    if api_changes:
        breaking_changes = [c for c in api_changes if c.get('type') == 'BREAKING']
        non_breaking_changes = [c for c in api_changes if c.get('type') != 'BREAKING']

        if breaking_changes:
            comment.append("h3. ⚠️ API Breaking Changes")
            comment.append("")
            comment.append("{warning}Breaking changes detected that will affect API consumers{warning}")
            comment.append("")

            for change in breaking_changes[:5]:  # Show top 5
                comment.append(f"h4. {{{{monospace}}}}{change.get('endpoint', 'Unknown')}{{{{monospace}}}}")
                comment.append(f"*Change:* {change.get('change', 'API modified')}")
                comment.append(f"*Impact Level:* {{color:red}}{change.get('impact', 'UNKNOWN')}{{color}}")
                comment.append(f"*Backward Compatible:* {'✅ Yes' if change.get('backward_compatible', False) else '❌ No'}")

                if change.get('affected_consumers'):
                    comment.append(f"*Affected Consumers:*")
                    for consumer in change['affected_consumers']:
                        comment.append(f"* {{{{monospace}}}}{consumer}{{{{monospace}}}}")

                if change.get('migration_notes'):
                    comment.append(f"*Migration Notes:* {change['migration_notes']}")

                comment.append("")

            if len(breaking_changes) > 5:
                comment.append(f"_{len(breaking_changes) - 5} more breaking changes in full report_")
                comment.append("")

            comment.append("----")
            comment.append("")

        if non_breaking_changes:
            comment.append("h4. ℹ️ Non-Breaking Changes")
            comment.append("The following API changes are backward compatible:")
            comment.append("")
            for change in non_breaking_changes[:5]:
                comment.append(f"* {{{{monospace}}}}{change.get('endpoint', 'Unknown')}{{{{monospace}}}}")

            if len(non_breaking_changes) > 5:
                comment.append(f"* ... and {len(non_breaking_changes) - 5} more")

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
    
    # Links to full reports (using absolute paths)
    import os
    report_dir = os.path.abspath('.ai-review')
    pr_number = metadata.get('pr_number', 'unknown')

    comment.append("h3. 📄 Full Reports")
    comment.append("")
    comment.append(f"[📊 Detailed HTML Report|file:///{report_dir}/pr-{pr_number}-data.html]")
    if os.path.exists(f".ai-review/pr-{pr_number}-data.json"):
        comment.append(f"[📋 Analysis Data (JSON)|file:///{report_dir}/pr-{pr_number}-data.json]")
    comment.append("")
    comment.append("----")
    comment.append("")

    # Footer
    comment.append(f"_Review ID: {metadata.get('review_id', 'N/A')}_")
    comment.append(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_")
    comment.append(f"_Generated by Code Review System_")
    
    return "\n".join(comment)

def save_jira_comment(data, output_file=None):
    """Save formatted JIRA comment to file (utility for workflow)

    Args:
        data: Dict with analysis results from workflow
        output_file: Optional output path (auto-generated if not provided)

    Returns:
        output_file path if successful, None otherwise
    """
    try:
        # Format comment from workflow data
        comment = format_jira_comment(data)
    except Exception as e:
        print(f"⚠️ Warning during comment formatting: {e}")
        # Generate minimal comment
        comment = f"""h1. PR Code Review Report

An error occurred while formatting the detailed JIRA comment.

_Report generated by automated PR Review Workflow_
"""

    # Determine output file
    if not output_file:
        try:
            pr_number = data.get('metadata', {}).get('pr_number', 'unknown')
            output_file = f".ai-review/pr-{pr_number}-jira-comment.txt"
        except Exception:
            output_file = ".ai-review/pr-unknown-jira-comment.txt"

    # Save comment
    try:
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(comment)

        print(f"✅ JIRA comment generated: {output_file}")
        print(f"📊 Comment length: {len(comment)} characters")

        jira_tickets = data.get('metadata', {}).get('jira_tickets', [])
        if jira_tickets:
            print(f"🎫 Ready to post to JIRA tickets: {', '.join(jira_tickets)}")
        else:
            print("⚠️ No JIRA tickets found in PR metadata")

        return output_file
    except Exception as e:
        print(f"❌ Error saving JIRA comment: {e}")
        return None

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

def post_jira_comment_via_mcp(jira_ticket, comment_text):
    """
    Post JIRA comment via Bitbucket MCP (Atlassian integration)

    Args:
        jira_ticket: JIRA ticket ID (e.g., 'PROJ-123')
        comment_text: Comment text to post

    Returns:
        bool: True if posted successfully, False otherwise
    """
    try:
        # NOTE: This function is designed to be called from Cascade workflow
        # It uses mcp0_postJiraComment (Atlassian/JIRA MCP)
        #
        # Workflow calls this via MCP:
        # result = mcp0_postJiraComment(ticket="{jira_ticket}", body="{comment_text}")
        #
        # This is a wrapper that documents the integration point.
        # Actual posting happens in the workflow via MCP calls.

        print(f"📤 Posting to JIRA ticket: {jira_ticket}")
        print(f"   Comment length: {len(comment_text)} chars")
        print(f"   (Actual posting handled by mcp0_postJiraComment in workflow)")

        return True

    except Exception as e:
        print(f"⚠️ Error posting to JIRA: {e}")
        return False

if __name__ == '__main__':
    # NOTE: This script is designed to be imported and used by the workflow.
    # It receives analysis_data directly from workflow execution.
    #
    # Example usage in workflow:
    # from jira_formatter import format_jira_comment, save_jira_comment
    # jira_comment = format_jira_comment(analysis_data)
    # save_jira_comment(analysis_data, ".ai-review/pr-123-jira-comment.txt")

    print("❌ This script is designed for workflow integration, not standalone use.")
    print("   Import the functions instead:")
    print("   - format_jira_comment(analysis_data) -> str")
    print("   - save_jira_comment(analysis_data, output_file) -> str")

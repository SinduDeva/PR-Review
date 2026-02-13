#!/usr/bin/env python3
"""
CLI Output Formatter for PR Code Review
Generates clean validation-focused output for Cascade CLI
"""

import json
import sys
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header():
    """Print review completion header"""
    print(f"\n{Colors.GREEN}✅ PR Code Review Complete{Colors.END}")
    print("━" * 70)

def print_summary(summary):
    """Print validation summary"""
    print(f"\n{Colors.BOLD}📋 VALIDATION RESULTS{Colors.END}\n")
    
    critical = summary.get('critical_issues', 0)
    high = summary.get('high_issues', 0)
    medium = summary.get('medium_issues', 0)
    low = summary.get('low_issues', 0)
    
    # Color-coded issue counts
    if critical > 0:
        critical_str = f"{Colors.RED}⚠️  {critical}{Colors.END}"
    else:
        critical_str = f"{Colors.GREEN}✅ {critical}{Colors.END}"
    
    if high > 0:
        high_str = f"{Colors.YELLOW}🟠 {high}{Colors.END}"
    else:
        high_str = f"{Colors.GREEN}✅ {high}{Colors.END}"
    
    print(f"Critical Issues: {critical_str}")
    print(f"High Priority:   {high_str}")
    print(f"Medium Priority: {Colors.CYAN}🟡 {medium}{Colors.END}")
    print(f"Low Priority:    {Colors.BLUE}🔵 {low}{Colors.END}")
    
    print("\n" + "━" * 70)

def print_pagination_info(pagination_metadata):
    """Print file retrieval pagination information"""
    if not pagination_metadata:
        return

    print(f"\n{Colors.BOLD}📊 FILE RETRIEVAL{Colors.END}\n")

    method = pagination_metadata.get('method', 'unknown')
    total = pagination_metadata.get('total_items_retrieved', 0)
    pages = pagination_metadata.get('pages_fetched', 1)
    truncated = pagination_metadata.get('truncated', False)
    max_pages_reached = pagination_metadata.get('max_pages_reached', False)

    print(f"  Method:           {method}")
    print(f"  Files Retrieved:  {total}")
    print(f"  API Pages Fetched: {pages}")

    if truncated or max_pages_reached:
        print(f"\n  {Colors.RED}⚠️ WARNING: Pagination limit reached{Colors.END}")
        print(f"  {Colors.RED}Results may be incomplete - manual verification recommended{Colors.END}")

    warnings = pagination_metadata.get('warnings', [])
    if warnings:
        print(f"\n  {Colors.YELLOW}Warnings:{Colors.END}")
        for warning in warnings:
            print(f"  → {warning}")

    # Show API call breakdown if multiple pages
    api_calls = pagination_metadata.get('api_calls_made', [])
    if len(api_calls) > 1:
        print(f"\n  API Call Breakdown:")
        for call in api_calls[:5]:  # Show first 5
            print(f"  → Page {call['page']}: {call['items_returned']} items")
        if len(api_calls) > 5:
            print(f"  → ... and {len(api_calls) - 5} more pages")

    print("\n" + "━" * 70)

def print_critical_findings(findings):
    """Print critical and high severity findings"""
    critical_findings = [f for f in findings if f['severity'] in ['CRITICAL', 'HIGH']]
    
    if not critical_findings:
        print(f"\n{Colors.GREEN}✅ No critical or high priority issues found!{Colors.END}\n")
        return
    
    print(f"\n{Colors.BOLD}{Colors.RED}🔴 CRITICAL & HIGH PRIORITY FINDINGS{Colors.END}\n")
    
    for finding in critical_findings:
        severity_color = Colors.RED if finding['severity'] == 'CRITICAL' else Colors.YELLOW
        
        print(f"{severity_color}{finding['id']}: {finding['title']}{Colors.END}")
        print(f"  → {finding['file']}:{finding['line']}")
        print(f"  → Impact: {finding['impact']}")
        
        # Show suggestion for critical issues
        if finding['severity'] == 'CRITICAL':
            print(f"  → {Colors.GREEN}Fix: {finding['suggestion']}{Colors.END}")
        
        print()

def print_spring_validation(validation):
    """Print Spring Boot validation scores"""
    print(f"{Colors.BOLD}🎯 SPRING BOOT VALIDATION{Colors.END}\n")
    
    scores = {
        'Architecture': validation.get('architecture', {}).get('score', 0),
        'Security': validation.get('security', {}).get('score', 0),
        'Performance': validation.get('performance', {}).get('score', 0),
        'Transactions': validation.get('transactions', {}).get('score', 0)
    }
    
    for category, score in scores.items():
        # Color based on score
        if score >= 8.0:
            status = f"{Colors.GREEN}✅{Colors.END}"
        elif score >= 6.0:
            status = f"{Colors.YELLOW}⚠️{Colors.END}"
        else:
            status = f"{Colors.RED}❌{Colors.END}"
        
        # Format score with padding
        score_str = f"{score:.1f}/10"
        print(f"  {category:14} {score_str:>7} {status}")
    
    print("\n" + "━" * 70)

def print_test_coverage(coverage):
    """Print test coverage analysis"""
    print(f"\n{Colors.BOLD}📊 TEST COVERAGE{Colors.END}\n")
    
    overall = coverage.get('overall', '0%')
    by_type = coverage.get('by_type', {})
    
    # Overall coverage
    overall_val = int(overall.rstrip('%'))
    if overall_val >= 80:
        overall_status = f"{Colors.GREEN}✅{Colors.END}"
    elif overall_val >= 60:
        overall_status = f"{Colors.YELLOW}⚠️{Colors.END}"
    else:
        overall_status = f"{Colors.RED}❌{Colors.END}"
    
    print(f"  Overall:      {overall:>5} {overall_status}")
    
    # By type
    for test_type, percentage in by_type.items():
        try:
            val = int(str(percentage).rstrip('%'))
            if val >= 75:
                status = f"{Colors.GREEN}✅{Colors.END}"
            elif val >= 50:
                status = f"{Colors.YELLOW}⚠️{Colors.END}"
            else:
                status = f"{Colors.RED}❌{Colors.END}"
        except (ValueError, AttributeError):
            status = "➖"
        
        print(f"  {test_type.capitalize():13} {percentage:>5} {status}")
    
    # Coverage gaps
    gaps = coverage.get('gaps', [])
    if gaps:
        print(f"\n  {Colors.YELLOW}Coverage Gaps: {len(gaps)} methods missing tests{Colors.END}")
    
    print("\n" + "━" * 70)

def print_api_impact(api_changes):
    """Print API impact analysis"""
    if not api_changes:
        return
    
    print(f"\n{Colors.BOLD}🔗 API IMPACT ANALYSIS{Colors.END}\n")
    
    breaking_changes = [c for c in api_changes if c['type'] == 'BREAKING']
    
    if breaking_changes:
        print(f"  {Colors.RED}Breaking Changes: {len(breaking_changes)}{Colors.END}")
        for change in breaking_changes:
            print(f"  → {change['endpoint']} ({change['change']})")
        
        # Affected consumers
        all_consumers = set()
        for change in breaking_changes:
            all_consumers.update(change.get('affected_consumers', []))
        
        if all_consumers:
            print(f"\n  {Colors.YELLOW}Affected Consumers:{Colors.END}")
            for consumer in all_consumers:
                print(f"  → {consumer}")
    else:
        print(f"  {Colors.GREEN}✅ No breaking API changes{Colors.END}")
    
    print("\n" + "━" * 70)

def print_recommendation(data):
    """Print overall recommendation"""
    rec_raw = data.get('overall_recommendation', 'APPROVE')
    if isinstance(rec_raw, dict):
        recommendation = rec_raw.get('decision', 'APPROVE')
        reason = rec_raw.get('reason', '')
        must_fix = rec_raw.get('must_fix', [])
    else:
        recommendation = rec_raw
        reason = data.get('overall_recommendation_reason', '')
        must_fix = []
    
    print(f"\n{Colors.BOLD}\u2705 RECOMMENDATION:{Colors.END} ", end='')
    
    if recommendation == 'APPROVE':
        print(f"{Colors.GREEN}\u2705 APPROVE{Colors.END}")
    elif recommendation == 'REQUEST_CHANGES':
        print(f"{Colors.RED}\u26a0\ufe0f REQUEST CHANGES{Colors.END}")
    else:
        print(f"{Colors.YELLOW}\u26a0\ufe0f APPROVE WITH COMMENTS{Colors.END}")
    
    if reason:
        print(f"\n{reason}")
    
    # Must-fix items (from dict or from recommendations list)
    if must_fix:
        print(f"\n{Colors.BOLD}Must Fix Before Merge:{Colors.END}")
        for i, item in enumerate(must_fix[:5], 1):
            print(f"  {i}. {item}")
    else:
        recommendations = data.get('recommendations', [])
        critical_recs = [r for r in recommendations if '\ud83d\udd34 CRITICAL' in r or '\ud83d\udfe0 HIGH' in r]
        if critical_recs:
            print(f"\n{Colors.BOLD}Must Fix Before Merge:{Colors.END}")
            for i, rec in enumerate(critical_recs[:3], 1):
                clean_rec = rec.replace('\ud83d\udd34 CRITICAL:', '').replace('\ud83d\udfe0 HIGH:', '').strip()
                print(f"  {i}. {clean_rec}")
    
    print("\n" + "\u2501" * 70)

def print_generated_files(metadata):
    """Print information about generated reports"""
    pr_number = metadata.get('pr_number')
    jira_tickets = metadata.get('jira_tickets', [])
    review_id = metadata.get('review_id', 'N/A')
    
    print(f"\n{Colors.BOLD}\u2704 Reports Generated:{Colors.END}")
    print(f"  → .ai-review/pr-{pr_number}-review.html")
    print(f"  → .ai-review/pr-{pr_number}-data.json")
    
    if jira_tickets:
        print(f"\n{Colors.BOLD}\u2708 JIRA Updated:{Colors.END}")
        for ticket in jira_tickets:
            print(f"  → Comment posted to {ticket}")
        print(f"  → Review ID: {review_id}")
    
    print("\n" + "\u2501" * 70 + "\n")

def format_cli_output(data_file):
    """Main function to format CLI output"""
    
    # Load review data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Print each section
    print_header()
    print_pagination_info(data.get('pagination_metadata'))
    print_summary(data['summary'])
    print_critical_findings(data['findings'])
    print_spring_validation(data['spring_boot_validation'])
    print_test_coverage(data['test_coverage'])
    print_api_impact(data['api_changes'])
    print_recommendation(data)
    print_generated_files(data['metadata'])

def format_compact_output(data):
    """Compact single-line output for CI/CD pipelines"""
    pr = data['metadata']['pr_number']
    critical = data['summary']['critical_issues']
    high = data['summary']['high_issues']
    coverage = data.get('test_coverage', {}).get('overall', 'N/A')
    rec_raw = data.get('overall_recommendation', 'APPROVE')
    rec = rec_raw.get('decision', 'APPROVE') if isinstance(rec_raw, dict) else rec_raw
    
    status_emoji = "\u2705" if rec == "APPROVE" else "\u26a0\ufe0f"
    
    print(f"{status_emoji} PR#{pr} | Critical: {critical} | High: {high} | Coverage: {coverage} | {rec}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python cli_formatter.py <review-data.json> [--compact]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    if '--compact' in sys.argv:
        with open(data_file) as f:
            format_compact_output(json.load(f))
    else:
        format_cli_output(data_file)

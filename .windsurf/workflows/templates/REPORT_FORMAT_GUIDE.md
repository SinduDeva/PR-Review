# Report Format Guide

## Overview

All reports (JIRA, HTML, CLI) follow a **consistent structure** and include **all completed analysis** before generation.

---

## Pre-Report Validation

**MUST occur BEFORE any report generation:**

```python
from analysis_validator import validate_analysis_completion, get_validation_report

# Validate analysis is complete
is_complete, missing_fields, warnings = validate_analysis_completion(analysis_data)

if not is_complete:
    report = get_validation_report(is_complete, missing_fields, warnings)
    print(report)
    # DO NOT PROCEED to report generation
    sys.exit(1)

# All analysis complete - proceed with reports
```

**Required Fields for Report Generation:**
- ✅ `metadata` - PR metadata (number, author, reviewer)
- ✅ `summary` - Issue counts and file statistics
- ✅ `findings[]` - Code analysis findings
- ✅ `overall_recommendation` - Approval decision with reason
- ✅ `impact_analysis` - Risk level and affected components

---

## Standard Report Structure

All reports follow this structure:

### 1. Header (Metadata)
```
PR #{pr_number}
Author: {author}
Reviewer: {reviewer}
Branch: {source} → {target}
Review Date: {date}
Review ID: {unique_id}
```

### 2. Summary Section
```
Files Changed:     {count}
Files Analyzed:    {count}
Files Skipped:     {count}
Lines Added/Del:   +{added} / -{deleted}

Issues Found:
  🔴 Critical: {count}
  🟠 High:     {count}
  🟡 Medium:   {count}
  🔵 Low:      {count}
```

### 3. Code Analysis (If Issues Found)
```
Critical & High Priority Issues ({count})

Issue: {id} - {title}
  Severity: {CRITICAL|HIGH}
  File: {path}:{line}
  Description: {description}
  Impact: {impact}
  Fix: {suggestion}

...top 5 issues shown, link to full report for rest...
```

### 4. Spring Boot Validation (If Applicable)
```
Architecture:   {score}/10 {status}
Security:       {score}/10 {status}
Performance:    {score}/10 {status}
Transactions:   {score}/10 {status}
```

### 5. Test Coverage (If Data Available)
```
Overall Coverage: {percentage}
  Unit Tests:        {percentage}
  Integration Tests: {percentage}
  E2E Tests:        {percentage}

Coverage Gaps: {count} methods missing tests
```

### 6. API Impact Analysis (If Changes Detected)
```
Breaking Changes: {count}
  - {endpoint} ({method}): {change}
    Impact Level: {HIGH|MEDIUM|LOW}
    Affected Consumers: {list}

Non-Breaking Changes: {count}
  - {endpoint}: {change}
```

### 7. Impact Analysis
```
Risk Level: {HIGH|MEDIUM|LOW}
Files Changed: {count}
Affected Components: {layers}
  Controllers:  {count}
  Services:     {count}
  Repositories: {count}
  Models:       {count}
```

### 8. Recommendations
```
Recommendation: {APPROVE|REQUEST_CHANGES|BLOCK}
Reason: {explanation}

Must Fix Before Merge:
  1. {item}
  2. {item}

Should Fix:
  - {item}
  - {item}
```

### 9. Footer (Links & Metadata)
```
Review ID: {unique_id}
Last Updated: {timestamp}
Full Reports:
  📊 Detailed HTML Report: {link}
  📋 Analysis Data: {link}
```

---

## Format by Channel

### JIRA Format (Markdown)
```
h1. Code Review - PR #123

|| Field || Value ||
| PR Author | john.doe |
| Reviewer | Automated Review System |
| Branch | feature/PROJ-123 → main |
| Review Date | 2024-01-15 |

h3. 📊 Summary
|| Metric || Value ||
| Files Changed | 5 |
| Critical Issues | 0 |
| High Priority | 1 |
| Test Coverage | 82% |

h3. 🔴 Critical & High Priority Issues (1)
[issue details]

h3. 🎯 Spring Boot Validation
[validation scores]

h3. 📈 Test Coverage
[coverage breakdown]

h3. 🔗 Affected APIs
[api changes]

h3. ✅ Recommendation
{panel:bgColor=#e3fcef}✅ APPROVE{panel}
Changes are ready to merge.

Must Fix Before Merge:
* Item 1

Should Fix:
* Item 2

h3. 📄 Full Reports
[📊 Detailed HTML Report]
[📋 Analysis Data (JSON)]
```

### HTML Format (Web)
- Professional styling with Bootstrap
- Collapsible sections
- Color-coded severity badges
- Interactive tables
- Responsive design
- Auto-opens in browser
- Fallback HTML if generation fails

### CLI Format (Terminal)
```
======================================================================
✅ CODE REVIEW ANALYSIS COMPLETE
======================================================================

🔍 FILE DETECTION METHOD
  ✓ Method: Git (local)
  ✓ Files Retrieved: 5

📊 VALIDATION RESULTS

Critical Issues: ✅ 0
High Priority:   🟠 1
Medium Priority: 🟡 2
Low Priority:    🔵 1

📋 CRITICAL & HIGH PRIORITY FINDINGS

SEC-001: Potential SQL Injection
  → src/service/UserService.java:45
  → Impact: HIGH
  Fix: Use parameterized queries

🎯 SPRING BOOT VALIDATION

Architecture   7.5/10 ⚠️
Security       8.5/10 ✅
Performance    6.0/10 ⚠️
Transactions   9.0/10 ✅

📈 TEST COVERAGE

Overall:          82% ✅
  Unit Tests:     85% ✅
  Integration:    78% ⚠️
  E2E Tests:      75% ⚠️

Coverage Gaps: 3 methods missing tests

🔗 API IMPACT ANALYSIS

Breaking Changes: 0 ✅
Non-Breaking Changes: 2

✅ RECOMMENDATION: APPROVE WITH COMMENTS

Changes are well-structured but consider:
1. Address performance concerns in cache layer
2. Add tests for new API endpoints

📋 Review Metadata:
  PR #: 123 | Author: john.doe
  Reviewer: Automated Review System
  Review ID: PR-123-20240115-143000

📊 Reports Generated:
  → .ai-review/pr-123-data.html
  → .ai-review/pr-123-data.json

🎫 JIRA Updated:
  → Comment posted to PROJ-123
```

---

## No Cascade Branding

Reports should NOT include:
- ❌ "Cascade", "Windsurf", "Claude"
- ❌ Tool-specific labels
- ❌ Plugin references

Reports SHOULD include:
- ✅ "Code Review System", "Automated Review System"
- ✅ "Code Review Analysis"
- ✅ PR number and author
- ✅ Reviewer information

---

## Consistent Field Naming

### Metadata Fields
```python
{
    "pr_number": 123,           # Always required
    "title": "PR title",        # PR title
    "author": "john.doe",       # PR author
    "reviewer": "Automated Review System",  # Always present
    "source_branch": "feature/...",
    "target_branch": "main",
    "branch": "feature/... → main",
    "review_date": "2024-01-15",
    "review_id": "PR-123-20240115-143000",
    "jira_tickets": ["PROJ-123", ...],
}
```

### Summary Fields
```python
{
    "files_changed": 5,
    "files_validated": 4,
    "files_excluded": 1,
    "lines_added": 250,
    "lines_deleted": 50,
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 2,
    "low_issues": 1,
}
```

### Recommendation Fields
```python
{
    "decision": "APPROVE",      # APPROVE|REQUEST_CHANGES|BLOCK
    "reason": "Changes...",
    "must_fix": [...]           # Critical items
    "should_fix": [...]         # High-priority items
}
```

---

## Example: Complete Report Flow

```python
# Step 8a: Build analysis_data in memory
analysis_data = {
    "metadata": {...},
    "summary": {...},
    "findings": [...],
    "overall_recommendation": {...},
    # All analysis fields populated
}

# Step 8b: VALIDATE before reporting
from analysis_validator import validate_analysis_completion
is_complete, missing, warnings = validate_analysis_completion(analysis_data)

if not is_complete:
    print("❌ Analysis incomplete - cannot generate reports")
    sys.exit(1)

print("✅ Analysis complete - generating reports")

# Step 8c: Execute reports in PRIORITY ORDER

# 1. POST JIRA
from jira_formatter import format_jira_comment
jira_comment = format_jira_comment(analysis_data)
post_jira_comment(ticket, jira_comment)
print("✅ JIRA comment posted")

# 2. GENERATE HTML
from generate_html import generate_html_report, save_html_report
save_html_report(analysis_data, ".ai-review/pr-123-data.html")
print("✅ HTML report generated")

# 3. PRINT CLI
from cli_formatter import format_cli_output
format_cli_output(analysis_data)
print("✅ CLI summary printed")

# 4. SAVE JSON (optional)
# json_saver.py handles this
print("✅ All reports generated")
```

---

## Validation Checklist

- [x] Analysis validation runs before report generation
- [x] No missing required fields in analysis_data
- [x] All three reports (JIRA, HTML, CLI) use consistent structure
- [x] No Cascade/Windsurf branding in reports
- [x] PR number and reviewer included in all reports
- [x] Metadata section present in all reports
- [x] Summary section includes issue counts and file stats
- [x] Code analysis included if findings exist
- [x] All analysis sections (Spring Boot, test coverage, APIs) if data available
- [x] Consistent recommendation format
- [x] Footer includes links and review metadata

# Report Format Standard

**ALL REPORTS MUST FOLLOW THIS STRUCTURE** (JIRA, HTML, CLI)

## Required Sections (in order)

### 1. HEADER / METADATA
- PR Number
- Title
- Author
- Reviewer (Automated Review System)
- Source Branch → Target Branch
- Review Date
- Execution Time

### 2. SUMMARY METRICS
- Files Changed
- Files Validated
- Files Excluded (test/docs)
- Lines Added
- Lines Deleted
- Issue Counts by Severity (Critical, High, Medium, Low)

### 3. CODE ANALYSIS FINDINGS
- Grouped by Severity (CRITICAL, HIGH, MEDIUM, LOW)
- For each finding:
  - Title/ID
  - Type (Bug, Security, Performance, Architecture, etc.)
  - File & Line Number
  - Description
  - Impact
  - Suggestion/Fix

### 4. SPRING BOOT VALIDATION
- Architecture Score & Status
- Security Score & Status
- Performance Score & Status
- Transaction Management Score & Status
- Issues for each category

### 5. TEST COVERAGE
- Overall Coverage %
- By Type (Unit, Integration, E2E)
- Coverage Gaps
- Missing Tests

### 6. API CHANGES
- Total Breaking Changes
- Total Non-Breaking Changes
- New Endpoints
- For each API change:
  - Endpoint (METHOD /path)
  - Change Type (BREAKING, NON_BREAKING, NEW)
  - Description
  - Affected Consumers
  - Migration Notes

### 7. IMPACT ANALYSIS
- Risk Level (HIGH, MEDIUM, LOW)
- Affected APIs
- Affected Components/Services
- Dependency Impact Summary
- Transitive Impact

### 8. RECOMMENDATIONS
- Overall Decision (APPROVE, REQUEST_CHANGES, BLOCK)
- Reason/Justification
- Must-Fix Items
- Should-Fix Items
- Action Items

### 9. POSITIVE OBSERVATIONS
- Strengths of the PR
- Best practices followed
- Good patterns used

### 10. AI SUMMARY
- Overall summary of changes and impacts
- Key takeaways

### 11. EXECUTION STATUS (OPTIONAL)
- Validation results
- Any warnings or partial failures
- Steps completed successfully

## Format Requirements

✅ **JIRA Comment**: Plain text, no unicode special chars (except emojis in descriptions)
✅ **HTML Report**: Professional styling, responsive design, collapsible sections
✅ **CLI Output**: ANSI colors (with detection), clear sections, formatted tables

## Content Requirements

✅ ALL reports must include ALL analysis data from Steps 4-5
✅ NO fields should be omitted from any report type
✅ Structure must be identical across all report types
✅ Same data, different format

## Validation Checklist

Before report is generated, verify:
- [ ] findings array is present (can be empty)
- [ ] spring_boot_validation exists
- [ ] test_coverage exists
- [ ] api_changes exists
- [ ] impact_analysis exists
- [ ] overall_recommendation exists
- [ ] metadata.pr_number exists
- [ ] metadata.author exists
- [ ] summary has all fields

If any field is missing → Block report generation

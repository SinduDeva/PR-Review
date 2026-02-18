# PR Detection, JIRA Generation, and Fallback Strategy

## Overview

This document describes the complete workflow for:
1. **PR Number Detection** - Automatic detection with CI/Git support
2. **JIRA Comment Generation** - Complete analysis in plain text
3. **Fallback Behavior** - Graceful exit if PR not found

---

## Step 1: PR Number Detection

### Detection Priority Order

```
1. CLI Argument (--pr 123)
     ↓ (if provided)
2. Environment Variables
     ├─ GitHub Actions (GITHUB_REF, GITHUB_EVENT_NAME)
     ├─ GitLab CI (CI_MERGE_REQUEST_IID)
     ├─ Bitbucket Cloud (BITBUCKET_PR_ID)
     ↓ (if found)
3. Git Branch Name Parsing
     ├─ PR-123 or PR/123
     ├─ feature/PR-123
     ├─ 123-description
     ├─ PROJ-123
     ↓ (if matched)
4. Git Commit Message Parsing
     ├─ "Merge pull request #123 from user/branch"
     ├─ "Merge branch 'feature/PR-123'"
     ↓ (if matched)
5. JSON Metadata (fallback)
     └─ analysis_data.metadata.pr_number
```

### Detection Logic Flow

```python
def _detect_pr_number(cli_pr=None):
    # Level 1: CLI
    if cli_pr > 0:
        return cli_pr  # ✅ Found

    # Level 2-4: PRDetector
    pr = detector.detect()
    if pr:
        return pr  # ✅ Found

    # Level 5: JSON
    pr = analysis_data.metadata.pr_number
    if pr > 0:
        return pr  # ✅ Found

    # Not found
    return None  # ❌ Fail
```

### Supported CI Systems

#### GitHub Actions

```yaml
# Triggered on pull_request
name: PR Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run PR Review
        run: python execution_orchestrator.py analysis.json
        # PR auto-detected from: GITHUB_REF (refs/pull/123/merge)
```

**Environment Variables Used:**
- `GITHUB_REF` = `refs/pull/123/merge` → Extracts `123`
- `GITHUB_EVENT_NAME` = `pull_request`

#### GitLab CI

```yaml
# Triggered on merge_request
include:
  - remote: 'https://example.com/templates.yml'

pr_review:
  stage: test
  script:
    - python execution_orchestrator.py analysis.json
    # PR auto-detected from: CI_MERGE_REQUEST_IID
```

**Environment Variables Used:**
- `CI_MERGE_REQUEST_IID` = `123`

#### Bitbucket Cloud

```yaml
image: python:3.9

pipelines:
  pull-requests:
    '**':
      - step:
          name: PR Review
          script:
            - python execution_orchestrator.py analysis.json
            # PR auto-detected from: BITBUCKET_PR_ID
```

**Environment Variables Used:**
- `BITBUCKET_PR_ID` = `123`

### Manual PR Number

If automatic detection fails or you want to override:

```bash
# Explicit PR number
python execution_orchestrator.py analysis.json --pr 123

# Environment variable
export PR_NUMBER=123
python execution_orchestrator.py analysis.json

# CI system
export GITHUB_REF=refs/pull/456/merge
python execution_orchestrator.py analysis.json
```

---

## Step 2: Execution Flow with PR Detection

### Complete Execution Order

```
START
  ↓
[Load Analysis Data]
  ↓
[Detect PR Number]
  ├─ Try CLI arg → Environment → Git → JSON → Fail?
  ├─ ✅ Found: Proceed
  ├─ ❌ Not Found: Exit with error
  ↓ (if found)
[PHASE 1: JIRA Update] (CRITICAL)
  ├─ Format entire analysis to plain text
  ├─ Save to: .ai-review/pr-{pr}-jira-comment.txt
  ├─ Post to JIRA (if uploader exists)
  ├─ ✅ Success: Continue
  ├─ ❌ Failure: Exit (CRITICAL)
  ↓
[PHASE 2: Database Update] (CRITICAL)
  ├─ Save analysis to database
  ├─ ✅ Success: Continue
  ├─ ❌ Failure: Exit (CRITICAL)
  ↓
[PHASE 3: CLI Generate] (SECONDARY)
  ├─ Generate CLI text output
  ├─ Save to: .ai-review/pr-{pr}-cli-output.txt
  ├─ ✅ Success: Continue
  ├─ ⚠️ Failure: Log warning, continue
  ↓
[PHASE 4: JSON Save] (SECONDARY)
  ├─ Save raw analysis JSON
  ├─ Save to: .ai-review/pr-{pr}-data.json
  ├─ ✅ Success: Continue
  ├─ ⚠️ Failure: Log warning, continue
  ↓
[PHASE 5: HTML Generate] (OPTIONAL)
  ├─ Generate HTML visual report
  ├─ Save to: .ai-review/pr-{pr}-data.html
  ├─ ✅ Success: Continue
  ├─ ⚠️ Failure: Log warning, continue
  ↓
[Print Summary]
  ├─ Critical phases status
  ├─ Secondary phases status
  ├─ Optional phases status
  ↓
END (SUCCESS or FAILURE)
```

### PR Detection Error Scenarios

#### Scenario 1: PR Found (Success)

```bash
$ python execution_orchestrator.py analysis.json

🔍 PR Detection...
✅ PR detected from CLI: 123

[PHASE 1/5] UPDATING JIRA (CRITICAL)...
✅ JIRA comment saved: .ai-review/pr-123-jira-comment.txt

[PHASE 2/5] UPDATING DATABASE (CRITICAL)...
✅ Database update successful

[PHASE 3/5] GENERATING CLI OUTPUT (SECONDARY)...
✅ CLI output generated

[PHASE 4/5] SAVING JSON (SECONDARY)...
✅ JSON saved: .ai-review/pr-123-data.json

[PHASE 5/5] GENERATING HTML (OPTIONAL)...
✅ HTML generated: .ai-review/pr-123-data.html

EXECUTION SUMMARY
✅ CRITICAL PHASES SUCCESSFUL - Workflow can continue
✅ Reports fully generated
```

#### Scenario 2: PR Not Found (Failure)

```bash
$ python execution_orchestrator.py analysis.json

🔍 PR Detection...
✅ Checking environment variables...
❌ No environment variables found
✅ Checking git branch name...
❌ No PR pattern found in branch
✅ Checking git commit message...
❌ No PR pattern found in commit
❌ PR number not found in any source

❌ Error: PR NUMBER NOT FOUND - Cannot proceed without PR number

Exit Code: 1
```

#### Scenario 3: Override with CLI

```bash
$ python execution_orchestrator.py analysis.json --pr 999

✅ PR detected from CLI: 999

[PHASE 1/5] UPDATING JIRA (CRITICAL)...
✅ JIRA comment saved: .ai-review/pr-999-jira-comment.txt
...
```

---

## Step 3: JIRA Comment Generation

### JIRA Comment Structure

The JIRA comment contains **ENTIRE analysis** in plain text format (no HTML, no links):

```
================================================================================
AUTOMATED PR REVIEW - PR #123
================================================================================

Title: Add authentication module
Branch: feature/auth
Author: developer@example.com
Review Date: 2026-02-18

SUMMARY METRICS
Files Changed: 5
Files Validated: 4
Files Excluded: 1
Lines Added: +234
Lines Deleted: -56

Issues Summary:
  Critical: 2
  High: 3
  Medium: 1
  Low: 0

FILES REVIEWED
File: src/auth/service.py
  Layer: service
  Status: ADDED
  Changes: +150 -0
  Summary: Authentication service implementation

... (20+ files with details)

FILES SKIPPED/EXCLUDED
1. .gitignore
2. README.md
... (complete list)

ALL FINDINGS (6 total)
CRITICAL (2):
  [FIND-001] Missing CSRF token validation
    Type: Security
    File: src/auth/service.py:45
    Description: OAuth callback missing CSRF protection
    Impact: Attackers could perform unauthorized authentication
    Suggestion: Add state parameter validation
    Fix: Implement state verification with secure random generation

  [FIND-002] SQL injection vulnerability
    Type: Security
    File: src/auth/handler.py:78
    Description: User input not sanitized in database query
    Impact: Database compromise possible
    Suggestion: Use parameterized queries
    Fix: Replace string concatenation with prepared statements

HIGH (3):
  [FIND-003] Unvalidated redirect
  [FIND-004] Missing rate limiting
  [FIND-005] Weak password validation

MEDIUM (1):
  [FIND-006] Missing documentation

IMPACT ANALYSIS
Affected Components:
  authentication: High risk
  user_service: Medium risk
  database: High risk

Backward Compatibility:
  Breaking: Yes
  Migration Required: Yes

Performance Impact:
  CPU: +5%
  Memory: +2MB
  Latency: +10ms

API CHANGES
Endpoint: POST /api/auth/login
  Method: POST
  Change: Added
  Description: New OAuth2 login endpoint

Endpoint: GET /api/user/{id}
  Method: GET
  Change: Modified
  Description: Added authentication requirement

... (all endpoints)

SPRING BOOT VALIDATION
architecture:
  score: 85
  status: GOOD

security:
  score: 72
  status: NEEDS_WORK

performance:
  score: 90
  status: EXCELLENT

transactions:
  score: 88
  status: GOOD

TEST COVERAGE
Unit Test Coverage: 85%
Integration Test Coverage: 72%
End-to-End Coverage: 45%
New Code Coverage: 92%

POSITIVE OBSERVATIONS
+ Well-structured service layer
+ Good separation of concerns
+ Comprehensive error handling
+ Clear variable naming
+ Good use of dependency injection

ANALYSIS SUMMARY
The authentication module implementation is well-architected with proper
separation of concerns and good error handling. However, critical security
issues must be addressed before merging:

1. CSRF protection missing from OAuth callback
2. SQL injection vulnerability in user query
3. Unvalidated redirects

The API changes are backward compatible for read operations but require
client updates for new endpoints. Test coverage is good (92% for new code)
but integration tests need expansion.

OVERALL RECOMMENDATION
Priority: HIGH
Status: REQUEST_CHANGES
Effort: Medium
Timeline: 1-2 days

RECOMMENDATION
ACTION REQUIRED: Review required (critical issues found)

================================================================================
```

### Key Features

**✅ Complete Coverage:**
- Metadata (title, branch, author, date)
- Summary metrics (all counts)
- Files reviewed (all files with changes)
- Files skipped (complete list)
- ALL findings (not just critical/high)
- Finding details (type, file, line, impact, fix)
- Impact analysis (full section)
- API changes (all endpoints)
- Spring Boot validation (all metrics)
- Test coverage (all metrics)
- Positive observations (what went well)
- AI summary (complete analysis)
- Overall recommendation (structured)
- Final recommendation (decision)

**✅ No HTML References:**
- No `.ai-review/` file paths
- No HTML report links
- No external file references
- Self-contained information
- Plain text only

**✅ Format Guarantees:**
- Plain text (no unicode, no markdown)
- Works in all JIRA versions
- Searchable with full-text indexing
- Printable without formatting issues
- No rendering problems

---

## Step 4: Fallback Behavior

### If PR Not Found

```
Step 1: PR Detection runs
  ↓
Step 2: Checks all 5 sources
  └─ CLI arg, Env vars, Git branch, Git commit, JSON
  ↓
Step 3: PR not found in any source
  └─ PRDetector returns None
  ↓
Step 4: ExecutionOrchestrator catches None
  └─ Raises ValueError("❌ PR NUMBER NOT FOUND...")
  ↓
Step 5: main() catches ValueError
  └─ Prints error and exits(1)
  ↓
Result: Workflow stops, no files created
```

### Error Message

```
❌ Error: PR NUMBER NOT FOUND - Cannot proceed without PR number

Tried:
  1. Environment variables (GitHub, GitLab, Bitbucket)
  2. Git branch name (PR-123, feature/PR-456, etc.)
  3. Git commit message (Merge pull request #123)

Provide with: --pr <number>
```

### What If Only JIRA is Critical?

**Current behavior:** If PR is not found, workflow stops immediately.

**Recommendation:** Consider environment where PR detection might fail:
- Local development (no git, no CI)
- Manual testing scripts
- Standalone usage

**Solution Options:**

Option A: Require explicit PR number
```bash
python execution_orchestrator.py analysis.json --pr 123
```

Option B: Create PR from branch (future enhancement)
```bash
python execution_orchestrator.py analysis.json --create-pr
# Creates PR-999 or uses suggested numbering
```

Option C: Allow "unknown" PR (not recommended for JIRA)
```bash
python execution_orchestrator.py analysis.json --allow-unknown-pr
# Creates .ai-review/pr-unknown-jira-comment.txt
```

---

## Step 5: Complete Workflow Checklist

### Pre-Execution

- [ ] Analysis data prepared (JSON format)
- [ ] PR number available or CI environment set up
- [ ] `.ai-review/` directory writable
- [ ] JIRA credentials configured (if posting to JIRA)
- [ ] Database connection available (optional)

### Execution

- [ ] PR number detected (CLI, env, git, or JSON)
- [ ] JIRA comment generated (PHASE 1) ← **CRITICAL**
- [ ] Database updated (PHASE 2) ← **CRITICAL**
- [ ] CLI output generated (PHASE 3) ← Optional
- [ ] JSON saved (PHASE 4) ← Optional
- [ ] HTML generated (PHASE 5) ← Optional

### Post-Execution

- [ ] JIRA comment in `.ai-review/pr-{pr}-jira-comment.txt`
- [ ] Analysis visible in JIRA issue
- [ ] Database records created
- [ ] CLI output available (if needed)
- [ ] JSON backup available (if needed)
- [ ] HTML report available (if needed)

---

## Step 6: Testing PR Detection

### Test Script

```bash
#!/bin/bash

# Test 1: CLI argument
python pr_detector.py --pr 123
# Expected: ✅ PR NUMBER: 123

# Test 2: No PR (should fail)
python pr_detector.py
# Expected: ❌ PR NOT FOUND

# Test 3: From git branch
git checkout -b PR-456-feature
python pr_detector.py
# Expected: ✅ PR NUMBER: 456

# Test 4: From git branch (alternative)
git checkout -b feature/PR-789
python pr_detector.py
# Expected: ✅ PR NUMBER: 789
```

### Test CI Environment Variables

```bash
# Test GitHub Actions
export GITHUB_REF=refs/pull/123/merge
python pr_detector.py
# Expected: ✅ PR NUMBER: 123

# Test GitLab CI
export CI_MERGE_REQUEST_IID=456
python pr_detector.py
# Expected: ✅ PR NUMBER: 456

# Test Bitbucket
export BITBUCKET_PR_ID=789
python pr_detector.py
# Expected: ✅ PR NUMBER: 789
```

---

## Step 7: Integration with CI/CD

### GitHub Actions

```yaml
name: Automated PR Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run PR Analysis
        run: python analyze_pr.py

      - name: Post JIRA Comment
        if: success()
        run: python execution_orchestrator.py .ai-review/pr-${{ github.event.pull_request.number }}-data.json
        # PR auto-detected from GITHUB_REF

      - name: Upload Artifacts
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: pr-review-${{ github.event.pull_request.number }}
          path: .ai-review/
```

### GitLab CI

```yaml
pr_review:
  stage: review
  script:
    - python analyze_pr.py
    - python execution_orchestrator.py .ai-review/pr-*.json
    # PR auto-detected from CI_MERGE_REQUEST_IID
  artifacts:
    paths:
      - .ai-review/
    reports:
      junit: .ai-review/results.xml
```

### Bitbucket Pipelines

```yaml
image: python:3.9

pipelines:
  pull-requests:
    '**':
      - step:
          name: PR Review
          script:
            - pip install -r requirements.txt
            - python analyze_pr.py
            - python execution_orchestrator.py .ai-review/pr-*.json
            # PR auto-detected from BITBUCKET_PR_ID
```

---

## Step 8: Summary and Best Practices

### ✅ What's Implemented

| Feature | Status | Details |
|---------|--------|---------|
| PR Detection | ✅ | 4-level fallback with CI support |
| CLI Integration | ✅ | `--pr` argument support |
| Environment Variables | ✅ | GitHub, GitLab, Bitbucket |
| Git Branch Parsing | ✅ | PR-123, feature/PR-456, etc. |
| Git Commit Parsing | ✅ | Merge PR message parsing |
| Graceful Failure | ✅ | Exit with error if not found |
| JIRA Comment | ✅ | Complete analysis, no HTML links |
| Entire Analysis | ✅ | 100% data coverage |
| Plain Text Format | ✅ | JIRA compatible |

### 📋 Best Practices

1. **Always Provide Context:**
   ```bash
   # Good - explicit PR number
   python execution_orchestrator.py analysis.json --pr 123

   # Good - git branch has PR info
   git checkout -b PR-456-feature
   python execution_orchestrator.py analysis.json

   # OK - CI environment has PR info
   # (In GitHub Actions, GitLab CI, etc.)

   # Bad - no PR information
   python execution_orchestrator.py analysis.json
   # ❌ Will fail: PR not found
   ```

2. **Handle Failures Gracefully:**
   ```bash
   python execution_orchestrator.py analysis.json || {
     echo "Workflow failed - check error above"
     exit 1
   }
   ```

3. **Verify JIRA Comment Content:**
   ```bash
   # Check what was posted to JIRA
   cat .ai-review/pr-123-jira-comment.txt | head -50

   # Should NOT contain:
   # - HTML report links
   # - .ai-review/ file paths
   # - External URLs

   # Should contain:
   # - All findings
   # - Impact analysis
   # - API changes
   # - Test coverage
   # - Recommendations
   ```

4. **Test in CI Environment:**
   ```yaml
   - name: Verify PR Detection
     run: |
       python pr_detector.py
       # Should output: ✅ PR NUMBER: {pr_number}
   ```

---

## Conclusion

### Key Takeaways

✅ **PR Detection:** Automatic with CI/Git fallback
✅ **JIRA Comment:** Complete analysis in plain text
✅ **No HTML Links:** Self-contained JIRA comment
✅ **Graceful Failure:** Exit early if PR not found
✅ **5-Phase Execution:** JIRA → DB → CLI → JSON → HTML
✅ **Priority Order:** Critical phases first

### Usage Examples

```bash
# CI Environment (auto-detect)
python execution_orchestrator.py analysis.json

# Manual with explicit PR
python execution_orchestrator.py analysis.json --pr 123

# Git-based detection
git checkout -b PR-456-feature
python execution_orchestrator.py analysis.json

# Test PR detection
python pr_detector.py
```

### Success Criteria

```
✅ PR number detected → Proceed
❌ PR number not found → Exit with error message
✅ JIRA comment generated → Success
✅ No HTML links in JIRA → Verified
✅ Complete analysis included → All data present
```

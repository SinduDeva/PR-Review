# HTML Report Generation - Test Checklist

Use this checklist to verify HTML report generation works correctly when running the workflow.

---

## Pre-Test Setup

- [ ] Git repository cloned and updated to latest
- [ ] Branch: `claude/stabilize-workflow-output-0Rb96` checked out
- [ ] Windsurf IDE open with PR-Review project
- [ ] Test PR created in Bitbucket (or use existing open PR)
- [ ] Test PR is in OPEN status (not draft)

---

## Test Execution

### 1. Run Workflow on Test PR

- [ ] In Windsurf, trigger the PR review workflow
- [ ] Ensure you're on the test PR's source branch
- [ ] Workflow starts with "Starting PR Analysis..."
- [ ] Steps 0-5 execute (Analysis phase)
  - [ ] Step 0: PR detection completes
  - [ ] Step 1: PR context gathered
  - [ ] Step 2: Files detected
  - [ ] Step 3: File categorization complete
  - [ ] Step 4: Code analysis complete (shows analysis running)
  - [ ] Step 5: Impact analysis complete

### 2. Step 6 - Report Generation Begins

- [ ] "STEP 1: WAIT FOR & VALIDATE ANALYSIS COMPLETION" displays
  - [ ] Validation checklist shown
  - [ ] All fields validated
  - [ ] "✅ Proceeding to report generation" message displayed

- [ ] "STEP 2: GENERATE JIRA COMMENT" executes
  - [ ] JIRA comment generated with all 11 sections
  - [ ] Comment posted to JIRA (if MCP configured)
  - [ ] "✅ JIRA comment posted" or "⚠️ JIRA posting attempted" displayed

- [ ] "STEP 3: GENERATE & AUTO-OPEN HTML REPORT" executes
  - [ ] HTML generation starts
  - [ ] "✅ HTML report generated: .ai-review/pr-{number}-data.html" displayed

### 3. HTML Auto-Open Behavior

**On Windows**:
- [ ] Browser automatically opens with HTML report
- OR
- [ ] Message displays with file path for manual opening

**On macOS**:
- [ ] Browser automatically opens with HTML report
- OR
- [ ] Message displays with file path for manual opening

**On Linux**:
- [ ] Browser automatically opens with HTML report (xdg-open)
- OR
- [ ] Message displays with file path for manual opening

**On Cascade Cloud IDE**:
- [ ] Message displays "📖 Open in browser: file://..." with file path
- [ ] User can copy-paste URL into browser

### 4. HTML Report Content Verification

Open the generated HTML report and verify all sections:

#### Section 1: HEADER / METADATA
- [ ] PR number displayed correctly
- [ ] PR title shown
- [ ] Author name visible
- [ ] Reviewer name shown (should be "Automated Review System" or actual reviewer)
- [ ] Review date present
- [ ] Execution time shown

#### Section 2: SUMMARY METRICS
- [ ] Metric boxes display in grid layout
- [ ] Files Analyzed count shown
- [ ] Lines Added count shown
- [ ] Lines Deleted count shown
- [ ] Critical, High, Medium, Low issue counts shown
- [ ] Color coding visible (red/orange/yellow/blue badges)

#### Section 3: CODE ANALYSIS FINDINGS
- [ ] If no issues: "✅ No issues detected" message shown
- [ ] If issues exist:
  - [ ] File sections are present
  - [ ] Files are expandable (click to toggle)
  - [ ] Issues grouped by severity within each file
  - [ ] Color-coded severity badges visible
  - [ ] Each issue shows: Title, Type, Line, Description, Impact, Fix

#### Section 4: SPRING BOOT VALIDATION
- [ ] Architecture score visible (0-10)
- [ ] Security score visible (0-10)
- [ ] Performance score visible (0-10)
- [ ] Transactions score visible (0-10)
- [ ] Pass/Warning/Fail status indicators present
- [ ] Color coding: Green (Pass), Orange (Warning), Red (Fail)

#### Section 5: TEST COVERAGE
- [ ] Overall Coverage percentage shown
- [ ] Unit Tests percentage shown
- [ ] Integration Tests percentage shown
- [ ] Coverage gaps listed (if any)
- [ ] Missing tests listed (if any)

#### Section 6: API CHANGES
- [ ] API changes count displayed
- [ ] Breaking changes count shown
- [ ] Non-breaking changes count shown (if any)
- [ ] New endpoints count shown (if any)

#### Section 7: IMPACT ANALYSIS
- [ ] Risk Level displayed (HIGH/MEDIUM/LOW with color coding)
- [ ] Affected APIs listed (if any)
- [ ] Affected Components listed (if any)
- [ ] Dependency Impact described
- [ ] Transitive Impact described

#### Section 8: RECOMMENDATIONS
- [ ] Decision displayed (APPROVE/REQUEST_CHANGES/BLOCK)
- [ ] Background color matches decision (green/orange/red)
- [ ] Reason/justification paragraph shown
- [ ] Must-Fix Items listed (if any)
- [ ] Should-Fix Items listed (if any)
- [ ] Action Items listed (if any)

#### Section 9: POSITIVE OBSERVATIONS
- [ ] Strengths listed (if any)
- [ ] Best Practices listed (if any)
- [ ] Good Patterns listed (if any)

#### Section 10: AI SUMMARY
- [ ] Overall Summary paragraph shown
- [ ] Key Takeaways listed (if any)

#### Section 11: EXECUTION STATUS
- [ ] Validation Results shown
- [ ] Warnings listed (if any)
- [ ] Steps Completed listed (0, 1, 2, 3, 4, 5)
- [ ] Generation timestamp shown

### 5. HTML Report Design Verification

- [ ] Report has professional appearance
- [ ] Colors are clear and readable
- [ ] No HTML special characters visible (proper escaping)
- [ ] Links work (if any)
- [ ] Expandable sections toggle smoothly
- [ ] Mobile view is readable (if checked on mobile)

### 6. File System Verification

- [ ] `.ai-review/` folder created
- [ ] File `pr-{number}-data.html` exists in `.ai-review/`
- [ ] File size is reasonable (> 50KB with content)
- [ ] File permissions allow reading
- [ ] File timestamp reflects current execution

### 7. Workflow Completion

- [ ] Step 6.3 (CLI summary) executes
  - [ ] CLI summary printed to Cascade output
  - [ ] Shows key findings in terminal format

- [ ] Step 6 completes with "✅ All reports generated successfully"
- [ ] Step 7 (Unlock) executes
  - [ ] Workflow file unlocked
  - [ ] "✅ Workflow unlocked" message shown

- [ ] Workflow completion message: "✅ PR Review Complete"

---

## Validation Verification

### Content Validation
- [ ] All 11 sections have content (not empty)
- [ ] No "N/A" or "undefined" values visible
- [ ] Numbers match across formats (JIRA, HTML, CLI)
- [ ] Analysis is comprehensive (findings, scores, impact)

### Format Validation
- [ ] HTML is valid and renders without errors
- [ ] No broken styling or layout issues
- [ ] Text is readable with good contrast
- [ ] Tables format correctly
- [ ] Lists display properly

### Data Validation
- [ ] PR metadata correct (number, title, author)
- [ ] File counts accurate
- [ ] Issue counts match findings count
- [ ] Severity breakdown is correct (sum of Critical+High+Medium+Low = total)
- [ ] Risk level matches findings severity

---

## Cross-Platform Testing

### Test on Multiple Systems

**If available, test on**:
- [ ] Windows 10/11
- [ ] macOS (Intel or Apple Silicon)
- [ ] Linux (Ubuntu/Debian recommended)
- [ ] Windsurf Cloud IDE (Cascade)

For each platform:
- [ ] HTML generates without errors
- [ ] Auto-open works (or file:// URL shown)
- [ ] Report displays correctly
- [ ] All sections visible and readable

---

## Re-Execution Testing

### Test Workflow Re-Running

- [ ] Run workflow first time → HTML generated
- [ ] Run workflow second time → HTML overwritten
  - [ ] File timestamp updated
  - [ ] Previous report replaced
  - [ ] No error messages
- [ ] Run workflow third time → Still works
  - [ ] No cooldown or restrictions
  - [ ] Unlimited re-runs allowed

---

## Error Scenario Testing

### Test Fallback Behaviors

**If browser auto-open fails**:
- [ ] Message displayed with file:// URL
- [ ] User can manually copy path to browser
- [ ] No workflow crash

**If HTML generation encounters error**:
- [ ] Fallback HTML generated with error details
- [ ] User is notified but workflow continues
- [ ] Other reports still generated (JIRA, CLI)

**If .ai-review folder doesn't exist**:
- [ ] Folder created automatically
- [ ] File saved successfully
- [ ] No permission errors

---

## Performance Verification

- [ ] HTML generation completes in reasonable time (< 5 seconds)
- [ ] File size is reasonable for content (typically 100-300KB)
- [ ] Browser opens quickly once auto-launch triggered
- [ ] Page renders without lag when expanding sections

---

## Issue Handling

### If Issues Found

1. **HTML doesn't auto-open**:
   - [ ] Check file:// URL is displayed as fallback
   - [ ] Manually open the file from `.ai-review/` folder
   - [ ] Verify content is correct even if auto-open fails

2. **Report sections missing**:
   - [ ] Check workflow logs for errors during analysis
   - [ ] Verify all 11 sections are in the HTML source
   - [ ] Confirm analysis steps (4-5) completed

3. **Styling issues**:
   - [ ] Check HTML renders correctly in different browsers
   - [ ] Verify CSS is embedded (no external file dependencies)
   - [ ] Test on mobile to verify responsiveness

4. **Data not showing**:
   - [ ] Verify analysis data exists (from Steps 0-5)
   - [ ] Check browser console for JavaScript errors
   - [ ] Confirm all required fields populated in analysis

---

## Sign-Off

**Tester Name**: _________________
**Test Date**: _________________
**Platform**: _________________
**Test Result**: ✅ PASS / ❌ FAIL

**Notes**:
```
[Space for test notes and observations]
```

---

## Final Verification

- [ ] All 11 sections verified on target platform
- [ ] HTML auto-opens or file:// URL provided
- [ ] Report content is accurate and complete
- [ ] Design is professional and readable
- [ ] Workflow completes successfully
- [ ] No errors in workflow execution

**Overall Status**: 🟢 READY FOR PRODUCTION / 🟡 NEEDS INVESTIGATION / 🔴 ISSUE FOUND

---

*This checklist ensures HTML report generation meets all requirements and works correctly in the workflow.*

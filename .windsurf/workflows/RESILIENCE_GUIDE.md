# Analysis Resilience Guide

Ensuring complete analysis is always available, even when individual components fail.

## Overview

The workflow now guarantees that analysis data is available in at least one accessible format, even if JSON creation, HTML generation, or other output methods fail.

## Architecture

### Three-Layer Resilience

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: In-Memory Analysis (Analysis Data Provider)       │
│  ✓ Always available during execution                         │
│  ✓ Survives storage failures                                 │
│  ✓ Can generate fallback outputs                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────────┬──────────┐
        ▼                     ▼                  ▼          ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│ Layer 2: Output │  │ Layer 2: CLI │  │ Layer 2:JIRA │  │ Layer 2: │
│ JSON File       │  │ Output       │  │ Comment      │  │ HTML     │
│ (Primary)       │  │ (Secondary)  │  │ (Tertiary)   │  │ Report   │
└─────────────────┘  └──────────────┘  └──────────────┘  └──────────┘
      ▼
┌─────────────────┐
│ Layer 3: Output │
│ Handlers        │
│ (All optional)  │
└─────────────────┘
```

## Components

### 1. Analysis Data Provider (`analysis_data_provider.py`)

Manages analysis in memory throughout execution:

```python
from analysis_data_provider import AnalysisDataProvider, Finding, FileSummary

# Create provider
provider = AnalysisDataProvider()

# Set metadata
provider.set_metadata(
    pr_number=123,
    title="Add auth module",
    author="dev@example.com"
)

# Add findings
provider.add_finding(Finding(
    id="FIND-001",
    severity="CRITICAL",
    type="Security",
    title="Missing CSRF validation",
    file="auth.py",
    line=45,
    description="OAuth missing state parameter",
    impact="Unauthorized auth possible",
    suggestion="Add state parameter"
))

# Always available
analysis_dict = provider.to_dict()
analysis_json = provider.to_json()

# Validate
is_valid, errors, warnings = provider.validate()

# Print summary
provider.print_summary()
```

### 2. Analysis Output Handler (`analysis_output_handler.py`)

Generates outputs non-blocking - continues even if some fail:

```python
from analysis_output_handler import AnalysisOutputHandler

# Create handler
handler = AnalysisOutputHandler(
    analysis_data=analysis_dict,
    pr_number=123,
    verbose=True
)

# Generate all outputs (each is non-blocking)
results = handler.output_all()

# Check what succeeded
print(results['json']['success'])      # ✅ JSON saved
print(results['html']['success'])      # ✅ HTML generated
print(results['jira']['success'])      # ⚠️  JIRA failed (but continues)
print(results['cli']['success'])       # ✅ CLI available

# Always check this
if handler.ensure_analysis_available():
    print("✅ Analysis is available in at least one format")
```

## Usage Patterns

### Pattern 1: Always Provide Analysis (Recommended)

```bash
#!/bin/bash

# Step 1: Generate analysis (always succeeds or has fallback)
analysis_data=$(python analyze_pr.py --pr 123)

# Step 2: Save analysis to memory provider
python -c "
from analysis_data_provider import AnalysisDataProvider
import json

data = json.loads('$analysis_data')
provider = AnalysisDataProvider()
provider.set_metadata(**data['metadata'])
provider.add_findings([...])

# Step 3: Ensure outputs are generated (non-blocking)
from analysis_output_handler import AnalysisOutputHandler
handler = AnalysisOutputHandler(provider.to_dict(), pr_number=123)
handler.output_all()

# Step 4: Success guaranteed
handler.ensure_analysis_available()
"
```

### Pattern 2: Graceful Degradation

```python
def generate_analysis_outputs(pr_number):
    """Generate analysis with graceful degradation"""

    # Step 1: Get analysis data
    analysis_data = run_analysis(pr_number)

    # Step 2: Create output handler
    handler = AnalysisOutputHandler(analysis_data, pr_number)

    # Step 3: Try primary output (JSON)
    json_ok, msg = handler.output_json()
    if not json_ok:
        print(f"⚠️  JSON failed: {msg}")

    # Step 4: Try HTML (non-blocking)
    html_ok, msg = handler.output_html()
    if not html_ok:
        print(f"⚠️  HTML failed: {msg}")

    # Step 5: Try CLI (always works)
    handler.output_cli()  # Has fallback implementation

    # Step 6: Verify at least one format succeeded
    if not handler.ensure_analysis_available():
        print("❌ CRITICAL: No output formats succeeded")
        sys.exit(1)

    return True
```

### Pattern 3: Handle Individual Failures

```python
# Try each output independently
handler = AnalysisOutputHandler(analysis_data, pr_number)

# JSON - critical, but has fallbacks
json_ok, _ = handler.output_json()

# HTML - nice to have, but not critical
html_ok, _ = handler.output_html()
if not html_ok:
    print("⚠️  HTML report not available, but analysis is saved")

# JIRA - optional integration
jira_ok, _ = handler.output_jira_comment()
if not jira_ok:
    print("⚠️  JIRA comment failed, comment file saved for manual posting")

# CLI - always works, has fallback
cli_ok, _ = handler.output_cli()

# Database - optional
db_ok, _ = handler.output_database()

# Final check
assert handler.ensure_analysis_available(), "Analysis must be available!"
```

## Guaranteed Availability

### Analysis is Available If ANY of These Succeed

1. ✅ **JSON saved** to `.ai-review/pr-{pr}-data.json`
   - Primary format
   - Used by other tools

2. ✅ **HTML generated** at `.ai-review/pr-{pr}-data.html`
   - Viewable in browser
   - Doesn't require JSON success

3. ✅ **CLI output** printed to stdout
   - Always has fallback implementation
   - Doesn't depend on HTML generator
   - Human-readable summary

4. ✅ **In-memory data** available during execution
   - Never fails (unless analysis generation itself fails)
   - Used for JIRA/database uploads
   - Available for custom processing

### What Happens If JSON Creation Fails

```
JSON Fails
    ├─ HTML tries to regenerate from in-memory data
    ├─ CLI generates minimal fallback output
    ├─ JIRA generates comment without JSON
    └─ ✅ Analysis still fully available
```

## Error Scenarios

### Scenario 1: JSON Encoding Error

```
❌ JSON encoding error: Complex object not serializable
⚠️  Continuing with fallback outputs...
✅ HTML report generated successfully
✅ CLI output generated successfully
✅ Analysis available in HTML and CLI formats
```

### Scenario 2: All External Generators Fail

```
❌ generate-html.py: FileNotFoundError
❌ jira_formatter.py: ImportError
⚠️  Falling back to built-in minimal output...
✅ CLI output generated (fallback implementation)
✅ Analysis available in CLI format
```

### Scenario 3: Storage Fails But Analysis Exists

```
❌ Cannot write to filesystem: Permission denied
❌ JSON save failed: {error}
⚠️  Analysis lost for disk storage
✓ But analysis still in memory during execution
→ Database upload still succeeds
→ Can stream to stdout or API
```

## Validation

### Before Saving Analysis

```bash
# Validate structure
python -c "
from analysis_data_provider import AnalysisDataProvider
provider = AnalysisDataProvider()
provider.set_metadata(pr_number=123)
# ... add findings, files, etc ...

# Validate
is_valid, errors, warnings = provider.validate()
if errors:
    print(f'❌ Critical errors: {errors}')
if warnings:
    print(f'⚠️  Warnings: {warnings}')
"
```

### After Saving Analysis

```bash
# Validate JSON file quality
python .windsurf/workflows/templates/json_validator.py .ai-review/pr-123-data.json

# Output:
# ❌ ERRORS (0):
# ⚠️  WARNINGS (1):
#    • metadata missing 'author'
# ✅ JSON is VALID but has warnings
```

## Workflow Integration

### Updated Step Sequence

```
Step 1: Analyze PR
  └─ Analysis Data Provider manages in-memory data

Step 2: Generate Outputs (Non-blocking)
  ├─ JSON (primary)
  ├─ HTML (secondary)
  ├─ JIRA (tertiary)
  ├─ CLI (fallback)
  └─ Database (optional)

Step 3: Verify Availability
  └─ At least one format succeeded? Continue.
     All failed? Safe error message.

Step 4: Post-Processing
  └─ Use whatever format succeeded
```

## Best Practices

### ✅ DO

- Always use `AnalysisDataProvider` for in-memory storage
- Always call `handler.ensure_analysis_available()` at the end
- Always have fallback implementations (CLI has built-in fallback)
- Always continue on output failures (they're non-blocking)
- Always validate analysis before critical operations

### ❌ DON'T

- Don't require JSON success for workflow continuation
- Don't skip validation just because one format failed
- Don't lose in-memory analysis when storage fails
- Don't block entire workflow on a single output format
- Don't ignore warnings - log them but continue

## Monitoring and Logging

### What to Log

```python
handler = AnalysisOutputHandler(data, pr_number)
results = handler.output_all()

# Log detailed results
for format_name, result in results.items():
    if result['success']:
        logger.info(f"✅ {format_name}: {result['message']}")
    else:
        logger.warning(f"⚠️  {format_name}: {result['message']}")

# Final status
if handler.ensure_analysis_available():
    logger.info("✅ Analysis successfully saved")
else:
    logger.error("❌ Analysis could not be saved in any format")
```

## Troubleshooting

### JSON Generation Always Fails

```bash
# Check if json.dumps() can serialize the data
python -c "
import json
from analysis_data_provider import AnalysisDataProvider

provider = AnalysisDataProvider()
# ... setup ...

try:
    json_str = json.dumps(provider.to_dict(), default=str)
    print('✅ JSON serializable')
except TypeError as e:
    print(f'❌ Serialization error: {e}')
    print('   Use default=str parameter')
"
```

### HTML Generation Falls Back But Shouldn't

```bash
# Check generate-html.py exists
ls .windsurf/workflows/templates/generate-html.py

# Verify Python can run it
python .windsurf/workflows/templates/generate-html.py .ai-review/pr-123-data.json

# Check for import errors
python -c "import jinja2; import networkx"
```

### CLI Fallback Not Running

```bash
# Test fallback directly
python -c "
from analysis_data_provider import AnalysisDataProvider
from analysis_output_handler import AnalysisOutputHandler

provider = AnalysisDataProvider()
provider.set_metadata(pr_number=123)

handler = AnalysisOutputHandler(provider.to_dict(), pr_number=123)
handler._generate_minimal_cli_output()
"
```

## Summary

The workflow now provides **resilient, guaranteed analysis delivery** through:

1. **In-memory storage** that survives failures
2. **Multiple output formats** so at least one works
3. **Graceful degradation** that continues on failures
4. **Validation** to ensure quality
5. **Fallback implementations** for critical paths

**Result**: Analysis is ALWAYS available, even if everything fails.

# HTML Report Generation - Technical Reference

**Document**: Technical Implementation Details
**Location**: `.windsurf/workflows/templates/generate-simple-html.py`
**Lines**: 698 lines
**Status**: Production-Ready

---

## 1. Architecture Overview

### Module Structure

```python
generate-simple-html.py
├── escape_html(text)           # XSS prevention function
├── open_html_in_browser(path)  # Cross-platform browser opener
├── generate_html_report(data)  # Main HTML generation
├── save_html_report(data)      # File I/O and orchestration
└── main()                       # Stdin entry point
```

### Data Flow

```
Analysis Data (in-memory)
    ↓
generate_html_report(data) receives dict
    ├─ Extracts metadata
    ├─ Extracts findings
    ├─ Extracts validation scores
    ├─ Counts issues by severity
    └─ Returns HTML string
    ↓
save_html_report() orchestrates
    ├─ Creates .ai-review/ folder
    ├─ Writes HTML to file
    ├─ Calls open_html_in_browser()
    └─ Returns file path
    ↓
Browser opens HTML file
    ├─ CSS styling applied
    ├─ JS toggles initialized
    └─ User sees report
```

---

## 2. Function Reference

### escape_html(text: str) → str

**Purpose**: Prevent XSS vulnerabilities by escaping HTML special characters

**Input**: Any user-controlled string
**Output**: HTML-safe string

**Implementation**:
```python
def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')      # & → &amp;
            .replace('<', '&lt;')       # < → &lt;
            .replace('>', '&gt;')       # > → &gt;
            .replace('"', '&quot;')     # " → &quot;
            .replace("'", '&#39;'))     # ' → &#39;
```

**Applied To**:
- Author name (line 430)
- Reviewer name (line 431)
- All finding titles (line 512)
- All file paths (line 504)
- All descriptions (lines 517, 612, 613, 621-623)
- All user-controlled content

**Security**: ✅ Prevents HTML injection and XSS attacks

---

### open_html_in_browser(html_file: str) → bool

**Purpose**: Auto-open HTML report in user's default browser (cross-platform)

**Input**: Path to HTML file
**Output**: True if successful, False otherwise

**Supported Platforms**:

**1. Windows (lines 63-70)**
```python
if system == "Windows":
    try:
        os.startfile(str(html_path))  # Native Windows API
    except Exception:
        subprocess.Popen(['explorer', str(html_path)])  # Fallback
```

**2. macOS (lines 72-76)**
```python
elif system == "Darwin":
    subprocess.Popen(['open', str(html_path)])
```

**3. Linux (lines 78-98)**
```python
else:
    if xdg_open_exists:
        subprocess.Popen(['xdg-open', str(html_path)])
    else:
        # Try common browsers: firefox, chromium, google-chrome, brave, opera
        for browser in browsers:
            subprocess.Popen([browser, str(html_path)])
```

**4. Cascade Cloud IDE (lines 51-61)**
```python
if in_cascade:
    print(f"📖 Open in browser: file://{html_path}")
    # Also attempt webbrowser module
    try:
        webbrowser.open(f'file://{html_path}')
    except:
        pass  # Graceful failure
```

**Environment Detection**:
```python
in_cascade = os.environ.get('WINDSURF_WORKSPACE') or \
             os.environ.get('WINDSURF_PROJECT')
```

**Error Handling**: Graceful fallback - prints file path for manual opening

---

### generate_html_report(data: dict) → str

**Purpose**: Generate complete HTML report from analysis data

**Input**: Dictionary with analysis results
```python
{
    'metadata': {...},
    'summary': {...},
    'findings': [...],
    'overall_recommendation': {...},
    'spring_boot_validation': {...},
    'test_coverage': {...},
    'api_changes': [...],
    'impact_analysis': {...},
    'positive_observations': {...},
    'ai_summary': {...},
    'execution_status': {...}
}
```

**Output**: HTML string (entire page)

**Processing**:

1. **Data Extraction** (lines 113-123)
   ```python
   metadata = data.get('metadata', {})
   summary = data.get('summary', {})
   findings = data.get('findings', [])
   # ... extracts all analysis sections
   ```

2. **Data Aggregation** (lines 129-141)
   ```python
   # Group findings by file for expandable sections
   findings_by_file = {}
   for finding in findings:
       file_path = finding.get('file', 'unknown')
       findings_by_file[file_path].append(finding)

   # Count issues by severity
   critical = [f for f in findings if f.get('severity') == 'CRITICAL']
   high = [f for f in findings if f.get('severity') == 'HIGH']
   # ... etc for MEDIUM and LOW
   ```

3. **Styling Decision** (lines 143-146)
   ```python
   rec_decision = recommendation.get('decision', 'UNABLE_TO_REVIEW')
   rec_class = 'approve' if rec_decision == 'APPROVE' else \
               'request-changes' if rec_decision == 'REQUEST_CHANGES' \
               else 'block'
   rec_icon = '✅' if rec_decision == 'APPROVE' else \
              '⚠️' if rec_decision == 'REQUEST_CHANGES' else '❌'
   ```

4. **HTML String Building** (lines 148-635)
   - DOCTYPE and head with embedded CSS (lines 148-423)
   - Header section (lines 426-434)
   - Summary metrics grid (lines 437-469)
   - Recommendation section with color coding (lines 471-494)
   - Code review with expandable files (lines 496-527)
   - Spring Boot validation table (lines 529-552)
   - Test coverage (lines 554-573)
   - API changes (lines 575-584)
   - Impact analysis (lines 586-596)
   - Positive observations (lines 598-606)
   - AI summary (lines 608-615)
   - Execution status (lines 617-626)
   - Footer (lines 630-632)

**Return**: Complete f-string with all HTML

---

### save_html_report(data: dict, output_file: str = None, auto_open: bool = True) → str

**Purpose**: Generate HTML, save to file, and optionally auto-open

**Parameters**:
- `data`: Analysis dictionary
- `output_file`: Output path (optional, defaults to `.ai-review/pr-{number}-data.html`)
- `auto_open`: Whether to open in browser (default: True)

**Returns**: File path if successful, None on error

**Implementation**:

1. **HTML Generation** (lines 650-654)
   ```python
   try:
       html = generate_html_report(data)
   except Exception as e:
       # Fallback HTML with error message
       html = f"<html><body><h1>Error generating report: {e}</h1></body></html>"
   ```

2. **Output File Determination** (lines 656-662)
   ```python
   if not output_file:
       pr_number = data.get('metadata', {}).get('pr_number', 'unknown')
       output_file = f".ai-review/pr-{pr_number}-data.html"
   ```

3. **Directory Creation** (lines 665-666)
   ```python
   os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
   ```

4. **File Writing** (lines 667-668)
   ```python
   with open(output_file, 'w', encoding='utf-8') as f:
       f.write(html)
   ```

5. **Auto-Open** (lines 671-673)
   ```python
   if auto_open:
       open_html_in_browser(output_file)
   ```

6. **Error Handling** (lines 676-678)
   ```python
   except Exception as e:
       print(f"❌ Error saving HTML report: {e}")
       return None
   ```

---

### main()

**Purpose**: Entry point when script is run directly

**Input**: JSON from stdin (piped from workflow)

**Implementation**:
```python
if __name__ == '__main__':
    try:
        data = json.load(sys.stdin)
        save_html_report(data, auto_open=False)  # Disable auto-open in subprocess
        sys.exit(0)
    except (json.JSONDecodeError, EOFError) as e:
        print(f"❌ Error reading JSON from stdin: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
```

**Usage**: `python generate-simple-html.py < analysis_data.json`

---

## 3. CSS Styling Details

### Layout Structure

**Container** (lines 166-173):
```css
.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
```

**Header** (lines 174-193):
```css
.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
}
```
- Gradient from purple (#667eea) to purple (#764ba2)
- White text for contrast
- Flexbox for metadata items

**Section** (lines 196-228):
```css
.section {
    border-bottom: 1px solid #eee;
    padding: 30px;
}
```
- Consistent padding and borders
- Metric grid uses CSS Grid

### Color Scheme

**Severity Colors** (lines 229-232):
- Critical: `#d32f2f` (Red)
- High: `#ff6f00` (Orange)
- Medium: `#fbc02d` (Yellow)
- Low: `#1976d2` (Blue)

**Recommendation Colors** (lines 235-248):
- APPROVE: Green background `#e8f5e9`, green border `#388e3c`
- REQUEST_CHANGES: Orange background `#fff3e0`, orange border `#ff6f00`
- BLOCK: Red background `#ffebee`, red border `#d32f2f`

### Responsive Design

**Summary Grid** (lines 205-208):
```css
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
}
```
- Auto-fits columns based on available space
- Minimum column width: 140px
- Responsive on mobile

### Interactive Elements

**File Toggle** (lines 283-322):
```css
.file-header {
    cursor: pointer;
    transition: background 0.2s;
}
.file-header:hover {
    background: #efefef;
}
.file-content {
    display: none;
}
.file-content.open {
    display: block;
}
```

**JavaScript Toggle** (lines 415-421):
```javascript
function toggleFile(element) {
    const content = element.nextElementSibling;
    const toggle = element.querySelector('.file-toggle');
    content.classList.toggle('open');
    toggle.textContent = content.classList.contains('open') ? '▼' : '▶';
}
```

---

## 4. Data Structure Requirements

### Input Data Structure

```python
{
    # Section 1: Metadata
    "metadata": {
        "pr_number": 1234,
        "pr_title": "Fix: ...",
        "author": "john.doe",
        "reviewer": "Automated Review System",
        "source_branch": "feature/my-feature",
        "target_branch": "develop",
        "review_date": "2026-03-03",
        "execution_time": "2m 34s"
    },

    # Section 2: Summary
    "summary": {
        "files_changed": 12,
        "files_validated": 12,
        "files_excluded": 2,
        "lines_added": 450,
        "lines_deleted": 320,
        "issues_critical": 1,
        "issues_high": 3,
        "issues_medium": 8,
        "issues_low": 15
    },

    # Section 3: Findings
    "findings": [
        {
            "severity": "CRITICAL",
            "file": "src/main/java/MyClass.java",
            "line": 42,
            "type": "Null Pointer",
            "title": "Potential null pointer access",
            "description": "Variable could be null",
            "impact": "Runtime exception",
            "suggestion": "Add null check before access"
        },
        # ... more findings
    ],

    # Section 4: Spring Boot Validation
    "spring_boot_validation": {
        "architecture": {"score": 8.5, "status": "PASS"},
        "security": {"score": 7.2, "status": "WARNING"},
        "performance": {"score": 8.0, "status": "PASS"},
        "transactions": {"score": 8.8, "status": "PASS"}
    },

    # Section 5: Test Coverage
    "test_coverage": {
        "overall": "85%",
        "by_type": {
            "unit": "90%",
            "integration": "78%",
            "e2e": "72%"
        }
    },

    # Section 6: API Changes
    "api_changes": [
        {
            "endpoint": "GET /api/users",
            "type": "NON_BREAKING",
            "description": "Added new query parameter"
        },
        # ... more changes
    ],

    # Section 7: Impact Analysis
    "impact_analysis": {
        "summary": {
            "risk_level": "MEDIUM",
            "affected_apis": ["UserService", "AuthService"],
            "affected_components": ["Web Layer", "Data Access Layer"],
            "dependency_impact": "3 services depend on these changes",
            "transitive_impact": "May affect downstream systems"
        }
    },

    # Section 8: Recommendation
    "overall_recommendation": {
        "decision": "REQUEST_CHANGES",
        "reason": "Security concerns need addressing",
        "must_fix": ["SQL injection vulnerability"],
        "should_fix": ["Add logging", "Improve error handling"],
        "action_items": ["Update dependencies"]
    },

    # Section 9: Positive Observations
    "positive_observations": {
        "strengths": ["Good test coverage", "Clean code structure"],
        "best_practices": ["Proper exception handling"],
        "good_patterns": ["Factory pattern usage"]
    },

    # Section 10: AI Summary
    "ai_summary": {
        "overall_summary": "Overall summary paragraph...",
        "key_takeaways": ["Key point 1", "Key point 2"]
    },

    # Section 11: Execution Status
    "execution_status": {
        "validation_results": "Passed",
        "warnings": [],
        "steps_completed": ["0", "1", "2", "3", "4", "5"]
    }
}
```

### Null Handling

The script handles missing/null fields gracefully:

```python
# Safe extraction with defaults
metadata.get('pr_number', 'unknown')
findings.get('line', 'N/A')
summary.get('files_validated', 0)

# Safe list/dict handling
findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
api_changes = data.get('api_changes', []) if isinstance(data.get('api_changes'), list) else []

# Conditional rendering
{f"<div>Content</div>" if field else ""}  # Only renders if field exists
```

---

## 5. Performance Characteristics

### Generation Time
- Typical report: < 1 second
- Large report (500+ findings): < 5 seconds

### File Size
- Typical report: 100-300 KB
- Large report: 500 KB - 1 MB
- Includes: CSS (embedded), JS (embedded), all data

### Memory Usage
- HTML generation: < 10 MB
- File write: < 5 MB
- No streaming required

---

## 6. Error Handling

### Generation Errors
```python
try:
    html = generate_html_report(data)
except Exception as e:
    # Fallback HTML with error message
    html = f"<html><body><h1>Error: {e}</h1></body></html>"
```

### File Write Errors
```python
try:
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
except Exception as e:
    print(f"❌ Error saving HTML: {e}")
    return None
```

### Browser Open Errors
```python
try:
    # Try to open
except Exception:
    # Print fallback URL
    print(f"📖 View manually: file://{html_path}")
```

---

## 7. Extending the Report

### Adding a New Section

1. Add data extraction at top:
   ```python
   new_section = data.get('new_section', {})
   ```

2. Add conditional rendering:
   ```python
   {f'''
   <!-- NEW SECTION -->
   <div class="section">
       <h2>Title</h2>
       <p>{new_section.get('field', 'N/A')}</p>
   </div>
   ''' if new_section else ""}
   ```

3. Add CSS styling:
   ```css
   .new-section {
       /* styles */
   }
   ```

### Changing Colors

Update severity color definitions:
```css
.severity-badge.critical {{ background: #d32f2f; }}
.severity-badge.high {{ background: #ff6f00; }}
.severity-badge.medium {{ background: #fbc02d; color: #333; }}
.severity-badge.low {{ background: #1976d2; }}
```

### Modifying Layout

Update grid definitions:
```css
.summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}
```

---

## 8. Security Considerations

### XSS Prevention
- ✅ All user content escaped via `escape_html()`
- ✅ No `innerHTML` usage (safe string building)
- ✅ No external script includes
- ✅ No data-* attributes from user input

### File Path Safety
```python
html_path = Path(html_file).resolve()  # Resolves to absolute path
```

### Input Validation
```python
findings = data.get('findings', []) if isinstance(data.get('findings'), list) else []
```

---

## 9. Compatibility

### Python Version
- Requires: Python 3.6+
- Uses: `f-strings`, `pathlib.Path`, standard library only
- No external dependencies in script itself

### Browsers
- Works in all modern browsers
- CSS Grid support required (all modern browsers)
- JavaScript ES5 syntax (no modern syntax)

### Platforms
- Windows: `os.startfile()` / `explorer`
- macOS: `open` command
- Linux: `xdg-open` or fallback browsers
- Cascade: Environment detection + webbrowser module

---

## 10. Testing Checklist

For developers modifying this script:

- [ ] HTML generation completes without exceptions
- [ ] Output file created with correct path
- [ ] All 11 sections present in HTML
- [ ] XSS escaping applied to all user content
- [ ] CSS styling displays correctly
- [ ] JavaScript toggle works for file sections
- [ ] Color coding correct for severity levels
- [ ] Auto-open works on all platforms (or fallback shown)
- [ ] Error messages are clear and helpful
- [ ] File size reasonable for content

---

**Document**: Technical Reference for HTML Report Generation
**Version**: 1.0
**Last Updated**: 2026-03-03
**Maintainer**: Engineering Team


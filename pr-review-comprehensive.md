---
auto_execution_mode: 3
description: Comprehensive PR Code Review with Token-Optimized Rich HTML Report & JIRA Integration
---

# PR Code Review - Comprehensive Analysis Workflow

## Overview
Enterprise-grade automated code review for Bitbucket Pull Requests with:
- **Automatic PR detection** from current Git branch
- **Code quality & security analysis**
- **Spring Boot best practices validation**
- **Change impact assessment (functionality, APIs)**
- **Test coverage validation**
- **AI-powered dependency graphs**
- **Rich HTML reporting (token-optimized)**
- **JIRA integration for report submission**

**Token Optimization**: HTML generation uses external templates - **ZERO HTML tokens in LLM context**

**Usage**: Invoke from Windsurf IDE - workflow auto-detects current branch and finds associated PR

---

## Prerequisites
- Bitbucket MCP server configured (`mcp1_*` tools)
- Atlassian/JIRA MCP server configured (`mcp0_*` tools)
- Python 3.8+ with dependencies: `jinja2`, `networkx`, `pygraphviz`
- Git repository with Bitbucket remote

---

## Workflow Steps

### Step 0: Auto-Detect Current Branch and PR
**Goal**: Identify the PR associated with current Git branch

**Actions**:
```bash
1. Get current branch name:
   git rev-parse --abbrev-ref HEAD

2. Search for PR by branch:
   Call: mcp1_getPullRequests(workspace, repo_slug) and filter by source branch name
   
3. Handle scenarios:
   - If 1 PR found: Use that PR → Continue to Step 1
   - If multiple PRs: Use the most recent OPEN PR → Continue to Step 1
   - If no PR found: STOP WORKFLOW
     Output: "❌ No PR found for branch '{branch_name}'. Please create a PR first."
     Exit gracefully without error
   
4. If PR found, extract PR number for subsequent steps
```

**Output if PR found**: 
```json
{
  "detected_branch": "{current_branch}",
  "pr_number": "{pr_number}",
  "pr_status": "OPEN"
}
```

**Output if no PR found**:
```
❌ No PR found for branch '{current_branch}'. Please create a PR first.
[WORKFLOW STOPS HERE]
```

---

### Step 1: Gather PR Context and Extract JIRA Tickets
**Goal**: Collect complete PR metadata and identify linked JIRA tickets

**Actions**:
```
1. Call: mcp1_getPullRequest(pr_number)
2. Extract:
   - PR title, description, author
   - Source → target branches
   - PR status, creation date
   - Creation timestamp for execution time tracking
   
3. Extract JIRA ticket IDs:
   Pattern: [A-Z]+-\d+
   Search in: PR title AND description
   Example matches: PROJ-123, TICKET-456, ABC-789
   
4. Handle JIRA scenarios:
   - If JIRA tickets found: Store for later use
   - If NO JIRA tickets found: Set jira_tickets = []
     Note: Review will continue, but JIRA posting will be skipped
     
5. Call: mcp1_getPullRequestComments(pr_number)
   - Capture existing review comments for context
```

**Output**: 
```json
{
  "pr_number": "{pr_number}",
  "title": "{pr_title}",
  "author": "{pr_author}",
  "jira_tickets": ["{extracted_ticket_ids}"],
  "source_branch": "{source_branch}",
  "target_branch": "{target_branch}",
  "created_at": "{timestamp}",
  "description": "{pr_description}"
}
```
If no JIRA tickets found, set `jira_tickets: []` and add `jira_warning` field. Review continues but JIRA posting will be skipped in Step 7.

---

### Step 2: Get Changed Files in PR (PR Changes Only)

**Goal**: Build complete list of ONLY files changed in this PR with their diffs

**IMPORTANT**: Analyze ONLY files modified in this PR, NOT the entire codebase.

**Primary Method** - Try Bitbucket diffstat:
```
Call: mcp1_getPullRequestDiffStat(pr_number)
If success: Extract file paths and stats (additions, deletions)
Result: List of changed files with modification counts
```

**Fallback Method** - Parse unified diff (when diffstat returns 404):
```
1. If mcp1_getPullRequestDiffStat returns 404/Not Found (common for large PRs), immediately switch to unified diff
   - Call: mcp1_getPullRequestDiff(pr_number)
   - Save the diff output path provided in MCP logs (Temp file path)
2. Parse diff content:
   - Split on "diff --git a/... b/..." markers
   - Extract file paths and content
   - Track additions / deletions manually by counting lines with leading '+' / '-'
3. Build file change objects with full diffs
4. Proceed to Step 3 with this reconstructed file list (mark source="unified diff" in logs)
```

**Output**: Array of ONLY changed files in this PR
```json
{
  "files": [
    {
      "path": "src/main/java/com/example/service/DataService.java",
      "additions": 45,
      "deletions": 12,
      "type": "MODIFY",
      "diff": "... full diff content ..."
    },
    {
      "path": "src/main/resources/application.yml",
      "additions": 3,
      "deletions": 1,
      "type": "MODIFY",
      "diff": "... full diff content ..."
    }
  ],
  "total_files": 12,
  "files_by_type": {
    "java": 8,
    "xml": 2,
    "yaml": 1,
    "sql": 1,
    "test": 0
  }
}
```

**Exclude from validation** (but include in impact analysis):
- Test files: `*Test.java`, `*Tests.java`, `src/test/**/*`
- Build files: `pom.xml`, `build.gradle` (unless config changes)
- Documentation: `*.md`, `*.txt` (unless affects behavior)

---

### Step 3: File Categorization & Technology Detection (PR Changes Only)

**Goal**: Classify ONLY PR-changed files for targeted analysis

**File Type Categories** (for validation):
1. **Java Source** - `*.java` (exclude test files)
   - Controllers, Services, Repositories, Models, DTOs
2. **XML Configuration** - `*.xml`
   - Spring config, MyBatis mappers, persistence.xml
3. **YAML Configuration** - `*.yml`, `*.yaml`
   - application.yml, application-*.yml
4. **SQL Scripts** - `*.sql`
   - Migrations, stored procedures, DDL
5. **Property Files** - `*.properties`
   - application.properties, messages.properties

**Excluded from validation** (but tracked for context):
- Test files: `src/test/**/*`, `*Test.java`, `*Tests.java`
- Build configs: `pom.xml`, `build.gradle` (note changes only)
- Documentation: `README.md`, `*.adoc`, `*.txt`

**Technology Detection** (on changed Java files):
```
- Spring Boot annotations (@Service, @RestController, @Entity, @Repository)
- JPA/Hibernate patterns (@OneToMany, @JoinColumn, EntityManager)
- Security configurations (@PreAuthorize, SecurityConfig)
- Async/reactive patterns (@Async, Mono, Flux)
- Transaction management (@Transactional)
- REST endpoints (@GetMapping, @PostMapping)
```

**Output**: Categorized file batches for validation
```json
{
  "validation_files": {
    "java_source": [
      "DataController.java",
      "DataService.java",
      "DataRepository.java"
    ],
    "xml_config": [
      "data-mapper.xml"
    ],
    "yaml_config": [
      "application.yml"
    ],
    "sql_scripts": [
      "V1.2__add_new_column.sql"
    ]
  },
  "excluded_files": {
    "test_files": [
      "DataServiceTest.java",
      "DataControllerTest.java"
    ],
    "documentation": [
      "README.md"
    ]
  },
  "technology_stack": {
    "spring_boot": true,
    "jpa_hibernate": true,
    "spring_security": false,
    "reactive": false
  }
}

---

### Step 4: Parallel Deep Analysis (PR Changed Files Only)

**Goal**: Conduct comprehensive code review on ONLY files changed in this PR

**CRITICAL**: Validate only non-test files (Java, XML, YAML, SQL, properties)

---

#### 4a: Java Source Code Validation (Enhanced Bug Detection)

**For each changed Java file** (excluding test files):

```
VALIDATE:

1. POTENTIAL BUGS & DEFECTS:
   
   NULL POINTER RISKS:
   - Dereferencing without null check
   - Method calls on potentially null objects
   - Unguarded array/collection access
   - Missing @NonNull/@Nullable annotations
   
   RESOURCE LEAKS:
   - Unclosed streams, readers, writers
   - Database connections not in try-with-resources
   - Missing close() in finally blocks
   - HttpClient connections not closed
   
   CONCURRENCY ISSUES:
   - Race conditions in shared state
   - Improper synchronization
   - Double-checked locking problems
   - Non-thread-safe collections in multi-threaded context
   
   EXCEPTION HANDLING BUGS:
   - Empty catch blocks
   - Catching generic Exception/Throwable
   - Swallowing exceptions without logging
   - Missing finally blocks for cleanup
   - Throwing in finally block
   
   LOGIC ERRORS:
   - Infinite loops (missing break/return)
   - Wrong comparison operators (= vs ==)
   - Incorrect boolean logic
   - Off-by-one errors in loops
   - Integer overflow potential
   - Division by zero possibility
   
   COLLECTION MISUSE:
   - ConcurrentModificationException risks
   - Iterating and modifying same collection
   - Wrong collection type for use case
   - Inefficient collection operations (contains in loop)
   
   STRING ISSUES:
   - String comparison with == instead of equals()
   - Missing null check before equals()
   - StringBuilder in loop instead of outside
   - Inefficient string concatenation in loops

2. SPRING BOOT BEST PRACTICES:
   
   ARCHITECTURE:
   - Proper layering (Controller → Service → Repository)
   - Dependency injection (constructor vs field injection)
   - Bean scope correctness (@RequestScope, @Singleton, @Prototype)
   - Configuration externalization (no hardcoded values)
   - Circular dependency detection
   
   SECURITY:
   - Input validation (@Valid, @Validated, @Pattern)
   - SQL injection prevention (parameterized queries)
   - Authentication/authorization checks (@PreAuthorize, @Secured)
   - Sensitive data handling (no plain text passwords)
   - CORS configuration safety
   - Path traversal vulnerabilities
   - Command injection risks
   
   PERFORMANCE:
   - N+1 query detection (lazy loading in loops)
   - Proper pagination implementation
   - Caching strategy (@Cacheable correctness)
   - Connection pool configuration
   - Lazy vs eager loading appropriateness
   - Large object creation in loops
   
   TRANSACTION MANAGEMENT:
   - @Transactional placement (service layer, not controller)
   - Transaction propagation correctness
   - Read-only optimization (readOnly=true for queries)
   - Rollback rules correctness
   - Transaction boundary violations
   - Long-running transactions
   
   ERROR HANDLING:
   - Global exception handlers (@ControllerAdvice)
   - Proper HTTP status codes
   - Error response consistency
   - Resource cleanup in exception scenarios

3. CODE QUALITY:
   
   MAINTAINABILITY:
   - Method complexity (cyclomatic complexity > 10)
   - Method length (> 50 lines)
   - Class size (> 500 lines)
   - Duplicated code blocks
   - Magic numbers/strings (use constants)
   - Meaningful variable/method names
   
   JAVA BEST PRACTICES:
   - Prefer composition over inheritance
   - Use interfaces for contracts
   - Avoid public fields (use getters/setters)
   - Override equals() and hashCode() together
   - Implement Comparable correctly
   - Use enums instead of int constants
   - Proper use of Optional
   - Stream API misuse
   
   LOGGING:
   - Appropriate log levels
   - No sensitive data in logs (PII, passwords)
   - Parameterized logging (use {} not +)
   - No System.out.println in production code
   - Exception logging with stack traces

For each issue found:
- Severity: CRITICAL/HIGH/MEDIUM/LOW
- File and line number
- Bug type and description
- Potential impact (runtime error, security, performance)
- Suggested fix with code example
```

**Output Example**:
```json
{
  "file": "DataService.java",
  "validations": [
    {
      "id": "BUG-001",
      "severity": "CRITICAL",
      "type": "NULL_POINTER_RISK",
      "line": 45,
      "description": "Potential NullPointerException: method getData() may return null",
      "code": "String value = data.getData().getValue();",
      "impact": "Runtime NullPointerException if getData() returns null",
      "fix": "Add null check:\nif (data.getData() != null) {\n  String value = data.getData().getValue();\n}"
    },
    {
      "id": "BUG-002",
      "severity": "HIGH",
      "type": "RESOURCE_LEAK",
      "line": 67,
      "description": "FileInputStream not closed - potential resource leak",
      "code": "FileInputStream fis = new FileInputStream(file);",
      "impact": "File handles not released, may cause 'Too many open files' error",
      "fix": "Use try-with-resources:\ntry (FileInputStream fis = new FileInputStream(file)) {\n  // use stream\n}"
    }
  ]
}
```

---

#### 4b: XML Configuration Validation

**For each changed XML file**:

```
VALIDATE:

SPRING XML CONFIG:
- Correct bean definitions
- Proper dependency injection setup
- Bean scope declarations
- Circular dependency detection
- Namespace declarations

MYBATIS MAPPERS:
- SQL injection in dynamic SQL
- ResultMap correctness
- Parameter mapping issues
- Missing type handlers
- Incorrect SQL syntax

PERSISTENCE.XML:
- JPA configuration correctness
- Database connection settings
- Dialect configuration
- Missing entity classes

XML STRUCTURE:
- Well-formed XML
- Valid against schema (if available)
- No sensitive data (passwords, keys)
```

---

#### 4c: YAML Configuration Validation

**For each changed YAML file** (application.yml, application-*.yml):

```
VALIDATE:

SYNTAX & STRUCTURE:
- Valid YAML syntax
- Correct indentation (spaces, not tabs)
- No duplicate keys
- Proper data types

SPRING BOOT CONFIG:
- Database connection settings
- Hardcoded credentials (flag as CRITICAL)
- Server port configuration
- Logging level settings
- Profile-specific overrides

SECURITY CONCERNS:
- Exposed passwords/API keys
- Debug mode in production profiles
- Insecure SSL/TLS settings
- Open CORS configuration

PERFORMANCE SETTINGS:
- Connection pool sizes
- Timeout configurations
- Cache settings
- Thread pool settings
```

---

#### 4d: SQL Script Validation

**For each changed SQL file**:

```
VALIDATE:

SQL SYNTAX:
- Valid SQL for target database
- Proper statement termination
- Correct data types
- Index definitions

MIGRATION SAFETY:
- Backward compatibility
- Data loss risks (DROP, TRUNCATE)
- Rollback strategy
- Performance impact of schema changes

SECURITY:
- No embedded credentials
- Proper user permissions
- SQL injection in dynamic SQL

PERFORMANCE:
- Missing indexes on foreign keys
- Index on large text columns
- Inefficient JOINs
- Missing WHERE clauses in updates
```

---

#### 4e: Property File Validation

**For each changed .properties file**:

```
VALIDATE:

STRUCTURE:
- Valid properties format
- No duplicate keys
- Character encoding issues

SECURITY:
- Hardcoded passwords
- API keys and secrets
- Database credentials
- Encryption keys

VALUES:
- Boolean values (true/false)
- Numeric values validity
- URL formats
- File path correctness
```

---

### Step 4f: API Change Impact Analysis (PR Changes Only)

**For API-related files changed in PR** (Controllers, DTOs):
```
Analyze ONLY changes in this PR:

BREAKING CHANGES:
- Removed endpoints or parameters
- Changed response structures
- Modified HTTP methods or paths
- Authentication requirement changes
- Required vs optional field changes

BACKWARD COMPATIBILITY:
- New optional vs required fields
- Default value handling
- API versioning strategy
- Deprecation notices

CONTRACTS:
- OpenAPI/Swagger documentation updates
- Request/response schema changes
- Error response modifications
- Content-Type changes

Identify Affected APIs:
- Endpoint paths changed
- HTTP methods modified
- Request/response DTOs altered
```

**Output**:
```json
{
  "api_changes": [
    {
      "endpoint": "POST /api/v1/data/process",
      "type": "BREAKING",
      "change": "Added required field in request body",
      "impact": "HIGH",
      "file": "DataController.java",
      "line": 45
    }
  ],
  "affected_endpoints": [
    "POST /api/v1/data/process",
    "GET /api/v1/data/{id}"
  ]
}
```

---

### Step 4g: Test Coverage Validation (Against Changed Files)

**For each non-test file changed in PR**:

```
Find corresponding test files:
- DataService.java → DataServiceTest.java
- DataController.java → DataControllerTest.java

Validate test coverage:

COVERAGE CHECKS:
- Does test file exist?
- Are new methods tested?
- Are edge cases covered?
- Are exception paths tested?
- Are integration tests present?

TEST QUALITY:
- Test isolation (no shared state)
- Assertion clarity (specific vs generic)
- Test data management
- Mock usage appropriateness

SPRING BOOT TESTING:
- Correct test slices (@WebMvcTest, @DataJpaTest)
- Application context loading efficiency
- Test transaction management
- Test property configuration
```

**Output**:
```json
{
  "file": "DataService.java",
  "test_file": "DataServiceTest.java",
  "test_coverage": {
    "new_methods": 3,
    "tested_methods": 2,
    "coverage_percentage": "67%",
    "gaps": [
      {
        "method": "processData",
        "reason": "Exception handling not tested"
      }
    ]
  }
}
```

---

### Step 5: Impact Analysis with Layered Dependency Graph

**Goal**: Analyze how PR changes impact the codebase using visual dependency graphs

**IMPORTANT**: 
- Analyze ONLY the files changed in this PR
- For impact analysis, scan ENTIRE codebase to find dependencies
- Create layered graph showing ripple effects

---

#### 5a: Build Multi-Layer Dependency Graph

**Layer Detection** (automatic based on file location and annotations):

```
LAYER 1 - CONTROLLERS (Color: Blue #3498db):
- Files with @RestController, @Controller
- Location: */controller/* or */web/*
- Example: DataController.java

LAYER 2 - SERVICES (Color: Green #2ecc71):
- Files with @Service
- Location: */service/*
- Example: DataService.java, ValidationService.java

LAYER 3 - REPOSITORIES (Color: Orange #e67e22):
- Files with @Repository, extends JpaRepository
- Location: */repository/* or */dao/*
- Example: DataRepository.java

LAYER 4 - MODELS/ENTITIES (Color: Purple #9b59b6):
- Files with @Entity, @Document
- Location: */model/* or */entity/*
- Example: Data.java, User.java

LAYER 5 - UTILITIES (Color: Gray #95a5a6):
- Utility classes, helpers
- Location: */util/* or */helper/*
- Example: DateUtils.java
```

**Dependency Extraction**:

```python
# Scan entire codebase to find:

1. Direct dependencies of changed files:
   - Import statements
   - Constructor/field injections (@Autowired)
   - Method parameters and return types

2. Files that depend on changed files (reverse dependencies):
   - Search all Java files for imports of changed classes
   - Find @Autowired references to changed beans
   - Identify method calls to changed APIs

3. Transitive dependencies:
   - Dependencies of dependencies (up to 3 levels deep)
```

**Graph Data Structure**:

```json
{
  "nodes": [
    {
      "id": "DataController",
      "label": "DataController.java",
      "layer": "CONTROLLER",
      "color": "#3498db",
      "status": "MODIFIED",
      "file_path": "src/main/java/com/example/controller/DataController.java",
      "changes": {
        "additions": 45,
        "deletions": 12
      }
    },
    {
      "id": "DataService",
      "label": "DataService.java", 
      "layer": "SERVICE",
      "color": "#2ecc71",
      "status": "MODIFIED",
      "file_path": "src/main/java/com/example/service/DataService.java",
      "changes": {
        "additions": 23,
        "deletions": 5
      }
    },
    {
      "id": "DataRepository",
      "label": "DataRepository.java",
      "layer": "REPOSITORY",
      "color": "#e67e22",
      "status": "UNCHANGED",
      "file_path": "src/main/java/com/example/repository/DataRepository.java"
    },
    {
      "id": "ValidationService",
      "label": "ValidationService.java",
      "layer": "SERVICE",
      "color": "#2ecc71",
      "status": "UNCHANGED"
    },
    {
      "id": "ReportService",
      "label": "ReportService.java",
      "layer": "SERVICE",
      "color": "#2ecc71",
      "status": "UNCHANGED"
    }
  ],
  "edges": [
    {
      "source": "DataController",
      "target": "DataService",
      "type": "depends_on",
      "relationship": "@Autowired"
    },
    {
      "source": "DataController",
      "target": "ValidationService",
      "type": "depends_on",
      "relationship": "@Autowired"
    },
    {
      "source": "DataService",
      "target": "DataRepository",
      "type": "depends_on",
      "relationship": "@Autowired"
    },
    {
      "source": "ReportService",
      "target": "DataService",
      "type": "depends_on",
      "relationship": "Method call"
    }
  ],
  "layers": {
    "CONTROLLER": ["DataController"],
    "SERVICE": ["DataService", "ValidationService", "ReportService"],
    "REPOSITORY": ["DataRepository"],
    "MODEL": [],
    "UTILITY": []
  }
}
```

---

#### 5b: Impact Propagation Analysis

**Analyze impact of changes**:

```
For each changed file:

1. DIRECT IMPACT:
   - Files that import this class
   - Files that inject this bean (@Autowired)
   - Files that call methods of this class

2. TRANSITIVE IMPACT (2-3 levels deep):
   - Files that depend on files that depend on changed file
   - Calculate impact distance (how many hops)

3. API CONSUMER IMPACT:
   - If Controller changed: Which endpoints affected?
   - If Service changed: Which controllers affected?
   - If Repository changed: Which services affected?

4. RISK ASSESSMENT:
   - High Risk: Many dependencies, core business logic
   - Medium Risk: Moderate dependencies, important features
   - Low Risk: Few dependencies, isolated changes
```

**Output**:
```json
{
  "impact_summary": {
    "files_changed": 3,
    "direct_impact": 5,
    "transitive_impact": 12,
    "total_affected_files": 20,
    "risk_level": "MEDIUM"
  },
  "impact_by_layer": {
    "CONTROLLER": 1,
    "SERVICE": 8,
    "REPOSITORY": 3,
    "MODEL": 2,
    "UTILITY": 1
  },
  "critical_paths": [
    {
      "path": ["DataController", "DataService", "DataRepository"],
      "description": "Main data processing flow",
      "risk": "HIGH"
    },
    {
      "path": ["DataController", "ValidationService"],
      "description": "Input validation flow",
      "risk": "MEDIUM"
    }
  ],
  "affected_apis": [
    {
      "endpoint": "POST /api/v1/data/process",
      "impact_level": "HIGH",
      "reason": "Core method signature changed in DataService"
    }
  ],
  "recommendations": [
    "Full regression testing recommended for data processing flows",
    "Update API documentation for endpoint changes",
    "Notify teams using POST /api/v1/data/process endpoint"
  ]
}
```

---

### Step 6: Aggregate Findings & Generate Reports

**Goal**: Create comprehensive, actionable reports with minimal tokens

#### 6a: Consolidate All Analysis Results

```
Merge findings from:
- Spring Boot validation
- API impact analysis
- Database impact
- Test coverage
- Dependency analysis
- Security scan
- Code quality checks

Deduplicate and prioritize by:
1. CRITICAL - Security, breaking changes, data loss
2. HIGH - Performance, API changes, missing tests
3. MEDIUM - Code quality, best practices
4. LOW - Style, documentation
```

#### 6b: Generate JSON Data File for Reports

**CRITICAL**: Save the consolidated review data as a JSON file. This JSON is consumed by `generate-html.py`, `jira_formatter.py`, and `cli_formatter.py`. All values below must be populated from actual analysis — use NO hardcoded examples.

**Save to**: `.ai-review/pr-{pr_number}-data.json`

**Required JSON Schema** (all fields populated from Steps 0-5):
```json
{
  "metadata": {
    "pr_number": "<from Step 0>",
    "title": "<from Step 1: PR title>",
    "author": "<from Step 1: PR author>",
    "source_branch": "<from Step 1>",
    "target_branch": "<from Step 1>",
    "branch": "<source_branch> → <target_branch>",
    "jira_tickets": ["<from Step 1: extracted ticket IDs, or empty array>"],
    "jira_warning": "<null if tickets found, else warning message>",
    "review_date": "<current ISO date>",
    "workflow_start_time": "<timestamp when Step 0 started>",
    "workflow_end_time": "<timestamp when Step 6 completes>",
    "execution_time_seconds": "<calculated difference>",
    "review_id": "PR-<pr_number>-<YYYYMMDD-HHMMSS>"
  },

  "summary": {
    "files_changed": "<total files in PR>",
    "files_validated": "<non-test, non-doc files analyzed>",
    "files_excluded": "<test + doc files skipped>",
    "lines_added": "<total additions across all files>",
    "lines_deleted": "<total deletions across all files>",
    "critical_issues": "<count from findings>",
    "high_issues": "<count from findings>",
    "medium_issues": "<count from findings>",
    "low_issues": "<count from findings>",
    "bugs_detected": "<total issues>",
    "test_coverage": "<overall % from Step 4g>",
    "test_coverage_overall": "<same as test_coverage>"
  },

  "findings": [
    {
      "id": "<auto-generated: BUG-001, SEC-001, PERF-001, etc.>",
      "severity": "<CRITICAL|HIGH|MEDIUM|LOW>",
      "type": "<category: NULL_POINTER_RISK, RESOURCE_LEAK, PII_LOGGING, etc.>",
      "title": "<short summary>",
      "file": "<full file path from PR>",
      "line": "<line number or N/A>",
      "description": "<detailed description of the issue>",
      "impact": "<what happens if not fixed>",
      "code_snippet": "<relevant code from the diff>",
      "suggestion": "<short fix description>",
      "suggested_fix": "<fix with code example>"
    }
  ],

  "files_reviewed": [
    {
      "path": "<file path from PR diff>",
      "lines_added": "<additions for this file>",
      "lines_deleted": "<deletions for this file>",
      "layer": "<CONTROLLER|SERVICE|REPOSITORY|MODEL|CONFIG|DATABASE|UTILITY>",
      "status": "<MODIFIED|ADDED|DELETED>",
      "summary": "<one-line change description>",
      "ai_summary": "<AI-generated description of what changed and why>",
      "dependencies": {
        "imports": ["<imported class names>"],
        "injected_beans": ["<@Autowired bean names>"],
        "called_by": ["<classes that depend on this file>"]
      },
      "test_coverage": {
        "test_file": "<corresponding test file name>",
        "exists": "<true|false>",
        "new_methods": "<count of new/changed methods>",
        "tested_methods": "<count of methods with tests>",
        "coverage_percentage": "<estimated %>",
        "missing_tests": [
          {
            "method": "<method signature>",
            "reason": "<why not tested>",
            "recommendation": "<suggested test approach>"
          }
        ]
      }
    }
  ],

  "files_skipped": [
    {
      "path": "<file path>",
      "reason": "<Test file|Documentation|Build config>"
    }
  ],

  "impact_analysis": {
    "summary": {
      "files_changed": "<count>",
      "direct_impact": "<count of directly dependent files>",
      "transitive_impact": "<count of transitively affected files>",
      "total_affected": "<total>",
      "risk_level": "<HIGH|MEDIUM|LOW>"
    },
    "by_layer": {
      "CONTROLLER": "<count>",
      "SERVICE": "<count>",
      "REPOSITORY": "<count>",
      "MODEL": "<count>",
      "UTILITY": "<count>"
    },
    "dependency_graph": {
      "nodes": [
        { "data": { "id": "<class>", "label": "<file>", "layer": "<layer>", "color": "<hex>", "status": "<MODIFIED|UNCHANGED>" } }
      ],
      "edges": [
        { "data": { "source": "<class>", "target": "<class>", "type": "depends_on" } }
      ]
    },
    "affected_apis": [
      {
        "endpoint": "<HTTP_METHOD /path>",
        "impact_level": "<HIGH|MEDIUM|LOW>",
        "change_type": "<BREAKING|NON_BREAKING|NEW>",
        "consumers": ["<known consumer names if any>"]
      }
    ],
    "affected_functionalities": [
      "<description of impacted business functionality from Step 5b>"
    ],
    "recommendations": [
      "<action items based on impact analysis>"
    ]
  },

  "api_changes": [
    {
      "endpoint": "<HTTP_METHOD /path>",
      "type": "<BREAKING|NON_BREAKING|NEW>",
      "change": "<what changed>",
      "impact": "<HIGH|MEDIUM|LOW>",
      "backward_compatible": "<true|false>",
      "affected_consumers": ["<consumer names>"],
      "migration_notes": "<guidance for consumers>"
    }
  ],

  "spring_boot_validation": {
    "architecture": { "score": "<0-10>", "status": "<PASS|WARNING|FAIL>", "issues": ["<descriptions>"] },
    "security":     { "score": "<0-10>", "status": "<PASS|WARNING|FAIL>", "issues": ["<descriptions>"] },
    "performance":  { "score": "<0-10>", "status": "<PASS|WARNING|FAIL>", "issues": ["<descriptions>"] },
    "transactions": { "score": "<0-10>", "status": "<PASS|WARNING|FAIL>", "issues": ["<descriptions>"] }
  },

  "test_coverage": {
    "overall": "<overall %>",
    "overall_status": "<PASS|WARNING|FAIL>",
    "by_type": {
      "unit": "<% or N/A>",
      "integration": "<% or N/A>",
      "e2e": "<% or N/A>"
    },
    "gaps": [
      { "file": "<source file>", "methods": ["<untested methods>"], "reason": "<explanation>" }
    ]
  },

  "overall_recommendation": {
    "decision": "<APPROVE|REQUEST_CHANGES|BLOCK>",
    "reason": "<explanation of decision>",
    "must_fix": ["<critical items that block merge>"],
    "should_fix": ["<high-priority improvements>"]
  },

  "recommendations": [
    "🔴 CRITICAL: <must-fix item>",
    "🟠 HIGH: <should-fix item>",
    "🟡 MEDIUM: <nice-to-have>",
    "🟢 LOW: <optional improvement>"
  ],

  "positive_observations": [
    "<positive aspects of the code changes>"
  ],

  "ai_summary": "<overall AI-generated summary of the PR changes and their impact>"
}
```

**IMPORTANT**: Do NOT put example/dummy data in the JSON. Every value must come from the actual analysis performed in Steps 0-5.

#### 6c: Generate HTML Report and CLI Output

**Actions** (execute these commands — do NOT skip):

```
1. Ensure .ai-review/ directory exists:
   mkdir -p .ai-review   (or New-Item -ItemType Directory -Force .ai-review on Windows)

2. Save the JSON from Step 6b to file:
   Write the complete JSON object to: .ai-review/pr-{pr_number}-data.json

3. Generate HTML report (ZERO LLM tokens — uses external template):
   python .windsurf/workflows/templates/generate-html.py .ai-review/pr-{pr_number}-data.json
   
   This reads pr-review-template.html and renders the full interactive report.
   Output: .ai-review/pr-{pr_number}-data.html

4. Generate JIRA comment file (for Step 7):
   python .windsurf/workflows/templates/jira_formatter.py .ai-review/pr-{pr_number}-data.json
   Output: .ai-review/pr-{pr_number}-jira-comment.txt

5. Print CLI summary:
   python .windsurf/workflows/templates/cli_formatter.py .ai-review/pr-{pr_number}-data.json

6. Open HTML report in browser:
   Invoke-Item .ai-review/pr-{pr_number}-data.html   # Windows
   open .ai-review/pr-{pr_number}-data.html           # macOS
```

**If Python scripts fail**: Fall back to displaying the CLI summary inline from the JSON data. The HTML report is the primary deliverable.

---

### Step 7: JIRA Integration - Submit Report (Conditional)

**Goal**: Post review report as JIRA comment IF tickets were found

**IMPORTANT**: This step is CONDITIONAL based on JIRA ticket detection

---

#### 7a: Check JIRA Ticket Availability

```
Check metadata.jira_tickets from Step 1:

If jira_tickets is EMPTY or NULL:
  - Skip JIRA posting entirely
  - Output: "⚠️ JIRA Integration Skipped — no tickets found in PR title/description"
  - Continue to workflow completion
  - Set jira_posted = false

If jira_tickets contains values:
  - Continue to JIRA posting (7b)
```

---

#### 7b: Post JIRA Comment

**Actions** (use `mcp0_*` Atlassian MCP tools):

```
For each JIRA ticket ID extracted in Step 1:

1. Get the Atlassian Cloud ID:
   Call: mcp0_getAccessibleAtlassianResources()
   Extract cloudId from the response.

2. Read the JIRA comment file generated in Step 6c:
   File: .ai-review/pr-{pr_number}-jira-comment.txt
   (Generated by jira_formatter.py — contains pre-formatted Markdown)

3. Post comment to JIRA:
   Call: mcp0_addCommentToJiraIssue(
     cloudId="{cloud_id}",
     issueIdOrKey="{ticket_id}",
     commentBody=<contents of jira-comment.txt>
   )

4. Handle results:
   - Success: Output "✅ Comment posted to {ticket_id}"
   - Failure: Log error, output "⚠️ Failed to post to JIRA: {error}"
     Save comment file for manual posting.
     Do NOT fail the workflow.
```

**IMPORTANT**: Do NOT hardcode any JIRA ticket IDs, PR numbers, or branch names in the comment body. The `jira_formatter.py` script generates the comment dynamically from the JSON data.

---

## Windsurf IDE Workflow Output

**The CLI output is generated by `cli_formatter.py` in Step 6c.** If the Python script fails, display an inline summary from the JSON data covering:

1. PR detection info (branch, PR number, JIRA tickets)
2. Severity breakdown (Critical/High/Medium/Low counts)
3. Top critical findings (file, line, description, fix)
4. Spring Boot validation scores
5. Test coverage summary
6. Impact analysis (affected files, APIs, risk level)
7. Overall recommendation
8. Report file paths
9. JIRA posting status
10. Next steps for the developer

**All values must come from the actual analysis data — never use hardcoded examples.**

---

## Token Optimization Breakdown

### Token Usage by Component:

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| HTML Template | 12,000 | 0 | 100% |
| CSS Styles | 3,000 | 0 | 100% |
| JavaScript | 2,000 | 0 | 100% |
| Report Generation | 500 | 50 | 90% |
| **TOTAL** | **17,500** | **50** | **99.7%** |

**How?**
1. HTML/CSS/JS in external template files (loaded by Python)
2. Dependency graph generated by Python (networkx)
3. LLM only generates minimal JSON data structure
4. All rendering done outside LLM context

---

## File Structure

```
.windsurf/workflows/
├── pr-review-comprehensive.md          # This workflow
└── templates/
    ├── pr-review-template.html         # Rich HTML Jinja2 template
    ├── generate-html.py                # HTML report generator (zero LLM tokens)
    ├── generate_pr_report.py           # Alternative HTML generator
    ├── jira_formatter.py               # JIRA comment formatter
    ├── cli_formatter.py                # CLI output formatter
    └── verify_setup.py                 # Setup verification script

.ai-review/                             # Generated per-run (gitignored)
├── pr-{pr_number}-data.json            # Review data JSON
├── pr-{pr_number}-data.html            # Generated HTML report
└── pr-{pr_number}-jira-comment.txt     # JIRA comment (for posting)
```

---

## Implementation Steps

### 1. Setup Template Files (One-time)

```bash
# Create template directory
mkdir -p .windsurf/workflows/templates/styles

# Download or create HTML template (not shown here - external file)
# Template includes: Bootstrap 5, Cytoscape.js, Chart.js, etc.
```

### 2. Run PR Review from Windsurf IDE

**Via Windsurf Workflow Panel:**
- Checkout your branch
- Open workflow panel
- Select this workflow
- Click Run

**Workflow automatically handles everything!**

### 3. View Results

**In Windsurf IDE:**
- Validation summary appears in output panel
- Click HTML report link to open in browser
- Check JIRA ticket for auto-posted comment

---

## Advanced Features

### Dependency Graph Visualization

**Using Cytoscape.js** (embedded in HTML):
```javascript
// Graph rendered in browser - zero LLM tokens
cytoscape({
  container: document.getElementById('dep-graph'),
  elements: {
    nodes: [
      { data: { id: 'DataService', type: 'modified' } },
      { data: { id: 'DataRepository', type: 'unchanged' } }
    ],
    edges: [
      { data: { source: 'DataService', target: 'DataRepository' } }
    ]
  },
  style: [
    {
      selector: 'node[type="modified"]',
      style: { 'background-color': '#ff6b6b' }
    }
  ]
});
```

### Interactive Filtering

**Client-side JavaScript** (in template):
```javascript
// Filter findings by severity, category, file
// No server/LLM involvement
function filterFindings(severity) {
  document.querySelectorAll('.finding-row').forEach(row => {
    row.style.display = 
      row.dataset.severity === severity ? 'table-row' : 'none';
  });
}
```

---

## Benefits Summary

✅ **Comprehensive Analysis**
- Spring Boot best practices
- API impact assessment
- Test coverage validation
- Security scanning
- Performance checks

✅ **Token Efficiency**
- 99.7% reduction in token usage
- Faster processing
- Lower API costs

✅ **Rich Reporting**
- Interactive HTML with graphs
- Professional UI design
- Export to PDF
- Print-friendly

✅ **JIRA Integration**
- Auto-post comments
- Override previous reviews
- Link to full reports
- Track review history

✅ **Developer Experience**
- Clear CLI validation output
- Actionable recommendations
- Visual dependency graphs
- One-click report access

---

## Usage from Windsurf IDE

**Invoke workflow from Windsurf:**

1. **Checkout your feature branch** in Windsurf IDE
2. **Open Workflow Panel** or Command Palette
3. **Run workflow:** "PR Code Review - Comprehensive Analysis"
4. **Workflow automatically:**
   - Detects current Git branch
   - Finds associated PR in Bitbucket
   - Extracts linked JIRA tickets
   - Runs complete analysis
   - Generates HTML report
   - Posts to JIRA

**No manual input required** - everything auto-detected!

**View results:**
- Validation output in IDE panel
- HTML report link in output
- JIRA comment auto-posted

The workflow auto-detects everything from the current Git branch. No manual input required.

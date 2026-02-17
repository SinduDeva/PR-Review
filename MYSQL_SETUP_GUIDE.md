# MySQL Database Setup & Testing Guide

This guide walks you through setting up MySQL for the PR Review workflow database integration.

## Overview

The PR Review workflow can persist all analysis results to a MySQL database for:
- **Audit Trail**: Complete history of all PR reviews
- **Historical Tracking**: Compare review results across multiple runs
- **Reporting**: Query and analyze trends in code quality
- **Integration**: Export data to other systems

## Prerequisites

- MySQL 5.7+ or MariaDB 10.3+
- Python 3.7+
- `mysql-connector-python` package

## Step 1: Install MySQL

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install mysql-server

# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql
```

### macOS (Homebrew)
```bash
brew install mysql

# Start MySQL service
brew services start mysql
```

### Windows
Download and install from: https://dev.mysql.com/downloads/mysql/

## Step 2: Install Python Connector

```bash
pip install mysql-connector-python
```

Verify installation:
```bash
python3 -c "import mysql.connector; print('✅ mysql-connector-python installed')"
```

## Step 3: Initialize Database

### Option A: Using SQL Script (Recommended)

```bash
# Log in to MySQL
mysql -u root

# Run the schema script
mysql -u root < .windsurf/workflows/templates/pr_review_audit_schema.sql

# Verify tables were created
mysql -u root pr_review_audit -e "SHOW TABLES;"
```

### Option B: Manual Setup

```bash
# Log in to MySQL
mysql -u root

# Create database
CREATE DATABASE pr_review_audit;

# Use the database
USE pr_review_audit;

# Create tables (copy-paste from pr_review_audit_schema.sql)
# See the SQL file for full schema
```

## Step 4: Test the Integration

### Run the Test Suite

```bash
cd .windsurf/workflows/templates

python3 test_database_uploader.py
```

This comprehensive test suite will:
1. ✅ Check if mysql-connector-python is installed
2. ✅ Generate sample PR review data
3. ✅ Test database connection
4. ✅ Test uploading data to the database
5. ✅ Verify data was inserted correctly

### Expected Output

```
======================================================================
  MySQL Database Integration Test Suite
======================================================================

======================================================================
  1. CHECKING DEPENDENCIES
======================================================================

✅ mysql-connector-python is installed

======================================================================
  2. GENERATING SAMPLE TEST DATA
======================================================================

✅ Generated sample test data
   File: .ai-review/test-pr-123-data.json
   PR #: 123
   Findings: 3
   Files: 3

======================================================================
  3. TESTING DATABASE CONNECTION
======================================================================

✅ Successfully connected to MySQL database
   Host: localhost
   Database: pr_review_audit

✅ Found 6 tables in database:
   - pr_review_run (0 rows)
   - pr_review_step (0 rows)
   - pr_review_file (0 rows)
   - pr_review_finding (0 rows)
   - pr_review_graph_node (0 rows)
   - pr_review_graph_edge (0 rows)

======================================================================
  4. TESTING DATABASE UPLOAD
======================================================================

✅ Successfully uploaded PR review to database!
   Run ID: 550e8400-e29b-41d4-a716-446655440000
   PR #: 123
```

## Step 5: Verify Data in Database

### View Uploaded Data

```bash
# Log in to MySQL
mysql -u root pr_review_audit

# View PR review summary
SELECT * FROM pr_review_run;

# View findings for a specific PR
SELECT severity, COUNT(*) as count FROM pr_review_finding GROUP BY severity;

# Use provided views and procedures
CALL sp_get_pr_review_history(123);
SELECT * FROM v_finding_statistics;
SELECT * FROM v_top_problematic_files;
```

## Step 6: Configuration

### Database Credentials

If you're using non-default credentials, update `database_uploader.py`:

```python
# Line 19 - Update default credentials
def __init__(self, host: str = 'localhost', user: str = 'your_user',
             password: str = 'your_password', db: str = 'pr_review_audit'):
```

Or pass arguments:
```bash
python database_uploader.py data.json --host 192.168.1.100 --db pr_review_audit
```

### Workflow Integration

The workflow will automatically upload to the database in **Step 8**:

```bash
python .windsurf/workflows/templates/database_uploader.py \
  .ai-review/pr-{pr_number}-data.json \
  --host localhost \
  --db pr_review_audit
```

If database is unavailable, the workflow logs a warning but continues.

## Database Schema

### Tables

| Table | Purpose | Rows/Run |
|-------|---------|----------|
| `pr_review_run` | Execution metadata, metrics | 1 |
| `pr_review_step` | Workflow step status | 8-9 |
| `pr_review_file` | Files reviewed | N (files changed) |
| `pr_review_finding` | Code issues found | M (findings) |
| `pr_review_graph_node` | Dependency graph nodes | X |
| `pr_review_graph_edge` | Dependency relationships | Y |

### Views (for reporting)

- `v_pr_review_summary` - Summary by PR number
- `v_finding_statistics` - Statistics by severity
- `v_top_problematic_files` - Files with most issues

### Stored Procedures

- `sp_get_pr_review_history(pr_number)` - Get all reviews for a PR
- `sp_get_run_findings(run_id)` - Get findings for a specific run
- `sp_calculate_run_metrics(run_id)` - Calculate metrics for a run

## Troubleshooting

### Connection Refused
```
Error: Connection refused to localhost:3306
```

**Solution**: MySQL is not running
```bash
# Linux
sudo systemctl start mysql

# macOS
brew services start mysql

# Windows - start from Services or command line
net start MySQL80
```

### Access Denied
```
Error: Access denied for user 'root'@'localhost'
```

**Solution**: Update credentials or reset password
```bash
# Reset root password (Linux/macOS)
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_password';"
```

### Database Not Found
```
Error: Unknown database 'pr_review_audit'
```

**Solution**: Create the database
```bash
mysql -u root -e "CREATE DATABASE pr_review_audit;"
mysql -u root < .windsurf/workflows/templates/pr_review_audit_schema.sql
```

### Tables Not Found
```
Error: Table 'pr_review_audit.pr_review_run' doesn't exist
```

**Solution**: Initialize the schema
```bash
mysql -u root pr_review_audit < .windsurf/workflows/templates/pr_review_audit_schema.sql
```

## Performance Considerations

### Database Size Growth
- **Per PR Review**: ~5-50 KB
- **1000 PR Reviews**: ~5-50 MB
- **Storage**: Minimal for most teams

### Recommended Maintenance

```bash
# Cleanup old reviews (older than 90 days)
mysql -u root pr_review_audit -e "
DELETE FROM pr_review_run
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
"

# Optimize tables (monthly)
mysql -u root pr_review_audit -e "OPTIMIZE TABLE pr_review_run;"

# Backup database (weekly)
mysqldump -u root pr_review_audit > backup_$(date +%Y%m%d).sql
```

## Advanced Queries

### Find all high-risk reviews
```sql
SELECT run_id, pr_number, started_at, critical_issues, high_issues
FROM pr_review_run
WHERE risk_level = 'HIGH'
ORDER BY started_at DESC;
```

### Trending issues
```sql
SELECT
    DATE(started_at) as review_date,
    COUNT(*) as total_reviews,
    SUM(critical_issues) as total_critical,
    ROUND(AVG(critical_issues), 2) as avg_critical_per_review
FROM pr_review_run
GROUP BY DATE(started_at)
ORDER BY review_date DESC;
```

### Files needing attention
```sql
SELECT
    file_path,
    COUNT(*) as issue_count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical
FROM pr_review_finding
WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY file_path
HAVING issue_count > 5
ORDER BY issue_count DESC;
```

## Next Steps

1. ✅ Complete steps 1-5 above
2. ✅ Run `test_database_uploader.py` to verify setup
3. ✅ Execute a real PR review with workflow
4. ✅ Query the database to see uploaded data
5. ✅ Set up automated backups
6. ✅ Create custom reports based on your needs

## Support

For issues or questions:
- Check the troubleshooting section above
- Review MySQL error messages in detail
- Verify all prerequisites are installed
- Check database credentials are correct
- Ensure database and tables were created successfully

---

**Last Updated**: 2026-02-17

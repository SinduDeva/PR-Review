#!/usr/bin/env python3
"""
MySQL Database Uploader Test Suite
Tests the database_uploader.py with sample PR review data
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_mysql_connector():
    """Check if mysql-connector-python is installed"""
    print_section("1. CHECKING DEPENDENCIES")

    try:
        import mysql.connector
        print("✅ mysql-connector-python is installed")
        return True
    except ImportError:
        print("❌ mysql-connector-python is NOT installed")
        print("\nTo install, run:")
        print("  pip install mysql-connector-python")
        return False


def generate_sample_data():
    """Generate sample PR review JSON data for testing"""
    print_section("2. GENERATING SAMPLE TEST DATA")

    sample_data = {
        "metadata": {
            "pr_number": 123,
            "title": "Add new authentication module",
            "author": "john.doe",
            "source_branch": "feature/PROJ-456-auth-module",
            "target_branch": "main",
            "branch": "feature/PROJ-456-auth-module → main",
            "review_date": datetime.now().strftime('%Y-%m-%d'),
            "review_id": f"PR-123-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "jira_tickets": ["PROJ-456"],
            "jira_ticket_id": "PROJ-456",
            "execution_time_seconds": 45
        },
        "pr": {
            "number": 123,
            "title": "Add new authentication module",
            "author": "john.doe",
            "source_branch": "feature/PROJ-456-auth-module",
            "target_branch": "main",
            "execution_time_seconds": 45
        },
        "summary": {
            "files_changed": 5,
            "files_validated": 5,
            "files_excluded": 0,
            "lines_added": 320,
            "lines_deleted": 45,
            "critical_issues": 1,
            "high_issues": 2,
            "medium_issues": 3,
            "low_issues": 1,
            "bugs_detected": 6,
            "test_coverage": "82%",
            "test_coverage_overall": "82%"
        },
        "workflow_start_time": (datetime.now() - timedelta(minutes=1)).isoformat(),
        "workflow_end_time": datetime.now().isoformat(),
        "files_reviewed": [
            {
                "path": "src/main/java/com/example/auth/AuthService.java",
                "layer": "service",
                "status": "MODIFIED",
                "additions": 150,
                "deletions": 20,
                "lines_added": 150,
                "lines_deleted": 20,
                "summary": "Added OAuth2 authentication service",
                "ai_summary": "Implements OAuth2 provider integration with proper error handling"
            },
            {
                "path": "src/main/java/com/example/auth/JwtValidator.java",
                "layer": "security",
                "status": "ADDED",
                "additions": 120,
                "deletions": 0,
                "lines_added": 120,
                "lines_deleted": 0,
                "summary": "JWT token validation utility",
                "ai_summary": "New JWT validator with RSA signature verification"
            },
            {
                "path": "src/test/java/com/example/auth/AuthServiceTest.java",
                "layer": "test",
                "status": "ADDED",
                "additions": 50,
                "deletions": 0,
                "lines_added": 50,
                "lines_deleted": 0,
                "summary": "Unit tests for auth service",
                "ai_summary": "Comprehensive test coverage for OAuth2 flows"
            }
        ],
        "files_skipped": [],
        "findings": [
            {
                "id": "FIND-001",
                "severity": "CRITICAL",
                "type": "Security",
                "title": "Missing CSRF token validation",
                "file": "src/main/java/com/example/auth/AuthService.java",
                "line": 45,
                "description": "OAuth callback endpoint missing CSRF protection",
                "impact": "Could allow attackers to perform unauthorized authentication",
                "suggestion": "Add state parameter validation in OAuth callback",
                "suggested_fix": "Implement state parameter verification using SecureRandom",
                "code_snippet": "response = client.exchangeCodeForToken(code); // Missing state check"
            },
            {
                "id": "FIND-002",
                "severity": "HIGH",
                "type": "Bug",
                "title": "Token refresh infinite loop possible",
                "file": "src/main/java/com/example/auth/AuthService.java",
                "line": 87,
                "description": "Refresh token endpoint doesn't prevent infinite loops",
                "impact": "Could cause stack overflow under certain conditions",
                "suggestion": "Add maximum refresh attempt counter",
                "suggested_fix": "Track refresh attempt count and reject after limit",
                "code_snippet": "while (!token.isValid()) { token = refreshToken(token); }"
            },
            {
                "id": "FIND-003",
                "severity": "HIGH",
                "type": "Performance",
                "title": "JWT validation happening on every request",
                "file": "src/main/java/com/example/auth/JwtValidator.java",
                "line": 23,
                "description": "JWT cryptographic validation performed without caching",
                "impact": "Could impact API response times under high load",
                "suggestion": "Cache validation results for short TTL",
                "suggested_fix": "Use Redis or local cache for recent tokens",
                "code_snippet": "validateSignature(token); // Called 1000x per second"
            }
        ],
        "spring_boot_validation": {
            "architecture": {
                "score": 8.5,
                "status": "PASS",
                "issues": []
            },
            "security": {
                "score": 7.0,
                "status": "WARNING",
                "issues": ["Missing CSRF protection in OAuth flow", "Token caching needed"]
            },
            "performance": {
                "score": 6.5,
                "status": "WARNING",
                "issues": ["JWT validation not cached"]
            },
            "transactions": {
                "score": 8.0,
                "status": "PASS",
                "issues": []
            }
        },
        "test_coverage": {
            "overall": "82%",
            "by_type": {
                "unit": "88%",
                "integration": "75%",
                "e2e": "60%"
            },
            "gaps": [
                {
                    "file": "src/main/java/com/example/auth/AuthService.java",
                    "methods": ["handleExpiredToken", "handleRefreshFailure"]
                }
            ]
        },
        "impact_analysis": {
            "summary": {
                "files_changed": 5,
                "direct_impact": "HIGH",
                "transitive_impact": "HIGH",
                "risk_level": "HIGH",
                "affected_endpoints": 12,
                "affected_consumers": 3
            },
            "affected_apis": [
                {
                    "endpoint": "/api/v1/auth/login",
                    "method": "POST",
                    "status": "MODIFIED",
                    "breaking": False
                },
                {
                    "endpoint": "/api/v1/auth/refresh",
                    "method": "POST",
                    "status": "NEW",
                    "breaking": False
                }
            ],
            "dependency_graph": {
                "nodes": [
                    {
                        "id": "AuthService",
                        "label": "AuthService.java",
                        "layer": "service",
                        "color": "blue",
                        "status": "modified",
                        "file_path": "src/main/java/com/example/auth/AuthService.java",
                        "properties": {"methods": 10, "lines": 250}
                    },
                    {
                        "id": "JwtValidator",
                        "label": "JwtValidator.java",
                        "layer": "security",
                        "color": "green",
                        "status": "added",
                        "file_path": "src/main/java/com/example/auth/JwtValidator.java",
                        "properties": {"methods": 5, "lines": 120}
                    }
                ],
                "edges": [
                    {
                        "source": "AuthService",
                        "target": "JwtValidator",
                        "type": "DEPENDS_ON",
                        "relationship": "uses",
                        "properties": {"calls": 8}
                    }
                ]
            }
        },
        "api_changes": [
            {
                "endpoint": "/api/v1/auth/oauth/callback",
                "method": "GET",
                "type": "BREAKING",
                "change": "Now requires state parameter",
                "impact": "HIGH",
                "backward_compatible": False,
                "migration_notes": "Add state parameter to all OAuth callbacks",
                "affected_consumers": ["mobile-app", "web-dashboard"]
            }
        ],
        "overall_recommendation": {
            "decision": "REQUEST_CHANGES",
            "reason": "Critical security issues must be resolved before merge",
            "must_fix": [
                "Add CSRF token validation in OAuth callback",
                "Implement state parameter verification"
            ],
            "should_fix": [
                "Add JWT validation caching",
                "Implement refresh token attempt limit"
            ]
        },
        "positive_observations": [
            "Good test coverage for main authentication flows",
            "Proper use of Spring Security annotations",
            "Clean separation of concerns with dedicated JWT validator"
        ],
        "ai_summary": "OAuth2 authentication module with good architecture but critical security issues in CSRF handling and token refresh logic that must be addressed before merge.",
        "execution_status": {
            "overall_status": "completed_with_warnings",
            "successful_steps": 7,
            "skipped_steps": 0,
            "failed_steps": 0,
            "execution_time_seconds": 45,
            "steps": [
                {
                    "step_key": "step_0_pr_detection",
                    "status": "success",
                    "attempted": True,
                    "fallback_used": False,
                    "error_message": None,
                    "note": "PR detected from branch name",
                    "started_at": (datetime.now() - timedelta(minutes=1)).isoformat(),
                    "finished_at": (datetime.now() - timedelta(minutes=1, seconds=2)).isoformat()
                },
                {
                    "step_key": "step_1_gather_context",
                    "status": "success",
                    "attempted": True,
                    "fallback_used": False,
                    "error_message": None,
                    "note": "PR context gathered successfully",
                    "started_at": (datetime.now() - timedelta(minutes=1)).isoformat(),
                    "finished_at": (datetime.now() - timedelta(minutes=1, seconds=5)).isoformat()
                }
            ],
            "warnings": [
                "JWT validation not cached - performance impact expected"
            ],
            "final_message": "Review completed with 1 critical issue found"
        }
    }

    # Save to file
    test_file = ".ai-review/test-pr-123-data.json"
    os.makedirs(".ai-review", exist_ok=True)

    with open(test_file, 'w') as f:
        json.dump(sample_data, f, indent=2)

    print(f"✅ Generated sample test data")
    print(f"   File: {test_file}")
    print(f"   PR #: 123")
    print(f"   Findings: {len(sample_data['findings'])}")
    print(f"   Files: {len(sample_data['files_reviewed'])}")

    return test_file, sample_data


def test_database_connection():
    """Test database connection"""
    print_section("3. TESTING DATABASE CONNECTION")

    try:
        import mysql.connector

        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='pr_review_audit'
            )
            cursor = conn.cursor()

            print("✅ Successfully connected to MySQL database")
            print("   Host: localhost")
            print("   Database: pr_review_audit")

            # Check if tables exist
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'pr_review_audit'
            """)

            tables = cursor.fetchall()
            if tables:
                print(f"\n✅ Found {len(tables)} tables in database:")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table[0]} ({count} rows)")
            else:
                print("\n⚠️  No tables found - database may need initialization")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\nMake sure:")
            print("  1. MySQL is running: mysql -u root")
            print("  2. Database exists: CREATE DATABASE pr_review_audit;")
            print("  3. Tables are created (see SQL schema)")
            return False

    except ImportError:
        print("❌ mysql-connector-python not installed")
        return False


def test_database_upload(json_file):
    """Test database upload with sample data"""
    print_section("4. TESTING DATABASE UPLOAD")

    try:
        from database_uploader import DatabaseUploader

        print(f"Loading sample data from: {json_file}")
        with open(json_file, 'r') as f:
            data = json.load(f)

        print(f"✅ Loaded {len(data['files_reviewed'])} files, {len(data['findings'])} findings")

        try:
            uploader = DatabaseUploader()
            run_id = uploader.upload(data)

            print(f"\n✅ Successfully uploaded PR review to database!")
            print(f"   Run ID: {run_id}")
            print(f"   PR #: {data['metadata']['pr_number']}")

            return True

        except Exception as e:
            print(f"\n❌ Upload failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Verify MySQL is running")
            print("  2. Check database and tables exist")
            print("  3. Verify user 'root' has permissions")
            return False

    except ImportError:
        print("❌ Could not import DatabaseUploader")
        print("   Make sure database_uploader.py is in the same directory")
        return False


def print_test_summary(results):
    """Print test results summary"""
    print_section("TEST SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"\nResults:")

    test_names = [
        "MySQL Connector Check",
        "Sample Data Generation",
        "Database Connection",
        "Database Upload"
    ]

    for i, name in enumerate(test_names):
        status = "✅ PASS" if results.get(f"test_{i}", False) else "❌ FAIL"
        print(f"  {status} - {name}")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Database integration is working.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. See details above.")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MySQL Database Integration Test Suite")
    print("="*70)

    results = {}

    # Test 1: Check dependencies
    results["test_0"] = check_mysql_connector()
    if not results["test_0"]:
        print("\n❌ Missing dependencies. Cannot continue with tests.")
        print_test_summary(results)
        return False

    # Test 2: Generate sample data
    json_file, sample_data = None, None
    try:
        json_file, sample_data = generate_sample_data()
        results["test_1"] = True
    except Exception as e:
        print(f"❌ Failed to generate sample data: {e}")
        results["test_1"] = False

    # Test 3: Test database connection
    results["test_2"] = test_database_connection()

    # Test 4: Test upload (only if connection works and data was generated)
    if results["test_2"] and results["test_1"]:
        results["test_3"] = test_database_upload(json_file)
    else:
        print_section("4. TESTING DATABASE UPLOAD")
        print("⏭️  Skipped (prerequisites not met)")
        results["test_3"] = False

    # Print summary
    print_test_summary(results)

    print("\n" + "="*70)
    print("  Next Steps")
    print("="*70)
    print("""
1. If all tests passed:
   ✅ Your database is configured correctly
   ✅ The workflow can upload PR reviews to the database
   ✅ You can query the pr_review_audit tables for reports

2. If tests failed:
   • Ensure MySQL is running
   • Create the database: mysql -u root
     > CREATE DATABASE pr_review_audit;
   • Run database schema setup (see CLAUDE.md for SQL)
   • Install connector: pip install mysql-connector-python

3. For production use:
   • Update database credentials in database_uploader.py
   • Test with real PR review data
   • Monitor database growth and set retention policies
""")

    return all(results.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

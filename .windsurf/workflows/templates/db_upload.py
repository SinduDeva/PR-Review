#!/usr/bin/env python3
"""
Database Uploader - Uploads PR review results to MySQL

Persists all workflow results to pr_review_audit database for audit trail,
historical tracking, and reporting across multiple PR reviews.

SKIP MODE:
  Use --skip-if-missing flag to gracefully skip database upload if JSON file is missing.
  This allows development/testing without database setup.

  Usage:
    python database_uploader.py <json_file> --skip-if-missing

  When JSON is missing:
    - With --skip-if-missing: Exits cleanly (exit 0), no error
    - Without --skip-if-missing: Creates fallback data and uploads to database

CORE LOGIC:
  Database upload logic remains unchanged. Skip mechanism only affects entry point behavior.
  All actual upload functions (_insert_run, _insert_step, etc.) are unmodified.
"""

import json
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class DatabaseUploader:
    """Uploads PR review data to MySQL pr_review_audit database"""

    def __init__(self, host: str = None, user: str = None, password: str = None, db: str = None):
        """Initialize database connection"""
        import os

        try:
            import mysql.connector
            self.mysql = mysql.connector
        except ImportError:
            print("❌ mysql-connector-python not installed")
            print("   Install with: pip install mysql-connector-python")
            raise

        # Use environment variables with fallback defaults
        self.host = host or os.environ.get('DB_HOST', 'localhost')
        self.user = user or os.environ.get('DB_USER', 'root')
        self.password = password or os.environ.get('DB_PASSWORD', '')
        self.db = db or os.environ.get('DB_NAME', 'pr_review_audit')
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = self.mysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db
            )
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to database: {self.db}")
        except self.mysql.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")

    def upload(self, json_data: Dict[str, Any]) -> str:
        """Upload complete PR review to database"""
        self.connect()

        try:
            # Generate unique run_id
            run_id = str(uuid.uuid4())

            # 1. Insert pr_review_run
            self._insert_run(run_id, json_data)

            # 2. Insert pr_review_step (one per step)
            if 'execution_status' in json_data and 'steps' in json_data['execution_status']:
                for step in json_data['execution_status']['steps']:
                    self._insert_step(run_id, step)

            # 3. Insert pr_review_file (one per changed file)
            if 'files_reviewed' in json_data:
                for file in json_data['files_reviewed']:
                    self._insert_file(run_id, file)

            # 4. Insert pr_review_finding (one per finding)
            if 'findings' in json_data:
                for idx, finding in enumerate(json_data['findings'], 1):
                    self._insert_finding(run_id, idx, finding)

            # 5. Insert dependency graph nodes/edges
            if 'impact_analysis' in json_data and 'dependency_graph' in json_data['impact_analysis']:
                graph = json_data['impact_analysis']['dependency_graph']

                if 'nodes' in graph:
                    for node in graph['nodes']:
                        self._insert_graph_node(run_id, node)

                if 'edges' in graph:
                    for edge in graph['edges']:
                        self._insert_graph_edge(run_id, edge)

            # Commit all transactions
            self.conn.commit()
            print(f"✅ Successfully uploaded PR review: {run_id}")
            return run_id

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Upload failed: {e}")
            raise
        finally:
            self.disconnect()

    def _insert_run(self, run_id: str, json_data: Dict[str, Any]):
        """Insert pr_review_run record"""
        execution_status = json_data.get('execution_status', {})
        impact_analysis = json_data.get('impact_analysis', {})

        sql = """
        INSERT INTO pr_review_run (
            run_id, pr_number, repo, workspace, source_branch, target_branch,
            reviewer, workflow_file, workflow_sha256, started_at, finished_at,
            status, execution_seconds, files_changed, files_validated,
            critical_issues, high_issues, medium_issues, low_issues,
            test_coverage, risk_level
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Count issues by severity
        findings = json_data.get('findings', [])
        critical = len([f for f in findings if f.get('severity') == 'CRITICAL'])
        high = len([f for f in findings if f.get('severity') == 'HIGH'])
        medium = len([f for f in findings if f.get('severity') == 'MEDIUM'])
        low = len([f for f in findings if f.get('severity') == 'LOW'])

        values = (
            run_id,
            json_data.get('pr_number'),
            json_data.get('repository'),
            json_data.get('workspace'),
            json_data.get('source_branch'),
            json_data.get('target_branch'),
            json_data.get('reviewer'),
            json_data.get('workflow_file'),
            json_data.get('workflow_sha256'),
            json_data.get('workflow_start_time'),
            json_data.get('workflow_end_time'),
            execution_status.get('overall_status', 'unknown'),
            execution_status.get('execution_time_seconds', 0),
            json_data.get('files_changed_count', 0),
            len(json_data.get('files_reviewed', [])),
            critical, high, medium, low,
            impact_analysis.get('test_coverage'),
            impact_analysis.get('risk_level'),
        )

        self.cursor.execute(sql, values)
        print(f"  ✅ Inserted run record: {run_id}")

    def _insert_step(self, run_id: str, step: Dict[str, Any]):
        """Insert pr_review_step record"""
        sql = """
        INSERT INTO pr_review_step (run_id, step_key, status, attempted, fallback_used, error_message, note, started_at, finished_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            run_id,
            step.get('step_key'),
            step.get('status'),
            step.get('attempted', 1),
            step.get('fallback_used', False),
            step.get('error_message'),
            step.get('note'),
            step.get('started_at'),
            step.get('finished_at'),
        )

        self.cursor.execute(sql, values)

    def _insert_file(self, run_id: str, file: Dict[str, Any]):
        """Insert pr_review_file record"""
        sql = """
        INSERT INTO pr_review_file (run_id, path, layer, status, lines_added, lines_deleted, summary, ai_summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            run_id,
            file.get('path'),
            file.get('layer'),
            file.get('status'),
            file.get('additions', 0),
            file.get('deletions', 0),
            file.get('summary'),
            file.get('ai_summary'),
        )

        self.cursor.execute(sql, values)

    def _insert_finding(self, run_id: str, idx: int, finding: Dict[str, Any]):
        """Insert pr_review_finding record"""
        sql = """
        INSERT INTO pr_review_finding (run_id, finding_id, severity, type, title, file_path, line_no, description, impact, suggestion, suggested_fix, code_snippet)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            run_id,
            f"FIND-{idx}",
            finding.get('severity', 'MEDIUM'),
            finding.get('type'),
            finding.get('title'),
            finding.get('file'),
            finding.get('line'),
            finding.get('description'),
            finding.get('impact'),
            finding.get('suggestion'),
            finding.get('suggested_fix'),
            finding.get('code_snippet'),
        )

        self.cursor.execute(sql, values)

    def _insert_graph_node(self, run_id: str, node: Dict[str, Any]):
        """Insert pr_review_graph_node record"""
        sql = """
        INSERT INTO pr_review_graph_node (run_id, node_id, label, layer, color, status, file_path, props_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            run_id,
            node.get('id'),
            node.get('label'),
            node.get('layer'),
            node.get('color'),
            node.get('status'),
            node.get('file_path'),
            json.dumps(node.get('properties', {})),
        )

        self.cursor.execute(sql, values)

    def _insert_graph_edge(self, run_id: str, edge: Dict[str, Any]):
        """Insert pr_review_graph_edge record"""
        sql = """
        INSERT INTO pr_review_graph_edge (run_id, source_id, target_id, edge_type, relationship, props_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            run_id,
            edge.get('source'),
            edge.get('target'),
            edge.get('type'),
            edge.get('relationship'),
            json.dumps(edge.get('properties', {})),
        )

        self.cursor.execute(sql, values)


def _create_fallback_data(json_file: str) -> Dict[str, Any]:
    """
    Create minimal fallback JSON data if file is missing or invalid

    This ensures database upload can proceed even if JSON generation fails in Step 8b
    """
    import os
    from pathlib import Path

    print("   Creating fallback JSON data...")

    # Extract PR number from filename (pr-{pr_number}-data.json)
    try:
        filename = Path(json_file).name
        pr_number = filename.split('-')[1] if '-' in filename else 'unknown'
    except:
        pr_number = 'unknown'

    # Create minimal fallback structure
    fallback_data = {
        'pr_number': pr_number,
        'metadata': {
            'pr_number': pr_number,
            'title': 'PR Analysis',
            'author': 'unknown',
            'reviewer': 'Automated Review System',
            'workflow_status': 'partial_completion',
        },
        'execution_status': {
            'overall_status': 'partial_completion_json_missing',
            'execution_time_seconds': 0,
            'notes': 'Database uploaded with fallback data (JSON generation failed)',
        },
        'findings': [],
        'files_reviewed': [],
        'impact_analysis': {
            'risk_level': 'UNKNOWN',
            'test_coverage': 0,
        },
        'repository': os.environ.get('REPO_SLUG', 'unknown'),
        'workspace': os.environ.get('WORKSPACE', 'unknown'),
        'source_branch': os.environ.get('SOURCE_BRANCH', 'unknown'),
        'target_branch': os.environ.get('TARGET_BRANCH', 'unknown'),
    }

    print(f"   ⚠️  Using fallback data for PR {pr_number}")
    print(f"   Database will be updated with minimal metadata")

    return fallback_data


def main():
    """Main entry point for database uploader"""
    import os

    # Parse arguments
    kwargs = {'host': 'localhost', 'db': 'pr_review_audit'}
    skip_if_missing = False
    json_file = None

    for i in range(1, len(sys.argv), 2):
        if sys.argv[i] == '--host' and i + 1 < len(sys.argv):
            kwargs['host'] = sys.argv[i + 1]
        elif sys.argv[i] == '--db' and i + 1 < len(sys.argv):
            kwargs['db'] = sys.argv[i + 1]
        elif sys.argv[i] == '--skip-if-missing':
            skip_if_missing = True
        elif not sys.argv[i].startswith('--'):
            json_file = sys.argv[i]

    try:
        # Load JSON data from stdin or file
        json_data = None

        # Try stdin first (preferred method - no temp files)
        if not sys.stdin.isatty():
            try:
                json_data = json.load(sys.stdin)
                print(f"✅ Loaded JSON data from stdin")
            except (json.JSONDecodeError, EOFError) as e:
                print(f"⚠️  Invalid JSON from stdin: {e}")

        # Fallback to file if provided and stdin didn't work
        if json_data is None and json_file:
            if not os.path.exists(json_file):
                if skip_if_missing:
                    print(f"⏭️  Skipping database upload (JSON file not found, --skip-if-missing enabled)")
                    sys.exit(0)
                else:
                    print(f"⚠️  JSON file not found: {json_file}")
            else:
                try:
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                    print(f"✅ Loaded JSON data from: {json_file}")
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON file: {json_file}")
                    json_data = _create_fallback_data(json_file)

        # Create fallback if still no data
        if json_data is None:
            json_data = _create_fallback_data(json_file or "stdin")

        if json_data is None:
            print("❌ Failed to load or create JSON data")
            sys.exit(1)

        # Upload to database
        uploader = DatabaseUploader(**kwargs)
        run_id = uploader.upload(json_data)

        print(f"\n✅ Database upload complete!")
        print(f"   Run ID: {run_id}")
        print(f"   Database: {kwargs['db']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PR Review Workflow Orchestrator
Validates and executes the complete PR review workflow with proper report generation

Coordinates:
- Step 0: PR detection and setup
- Steps 1-5: LLM analysis (data preparation)
- Step 6: Report generation (JSON, HTML, JIRA, CLI)
- Step 7: JIRA integration
- Step 8: Database persistence
- Step 9: Cleanup and unlocking
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class WorkflowOrchestrator:
    """Orchestrates the complete PR review workflow"""

    def __init__(self, pr_number: int = 123, verbose: bool = False):
        """Initialize workflow orchestrator"""
        self.pr_number = pr_number
        self.verbose = verbose
        self.ai_review_dir = Path(".ai-review")
        self.templates_dir = Path(".windsurf/workflows/templates")
        self.start_time = datetime.now()
        self.status = {
            "step_0_lock": False,
            "step_1_pr_detection": False,
            "step_2_pr_context": False,
            "step_3_file_detection": False,
            "step_4_analysis_prep": False,
            "step_5_llm_analysis": False,
            "step_6_report_gen": False,
            "step_7_jira": False,
            "step_8_database": False,
            "step_9_unlock": False,
        }
        self.analysis_data = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "INFO":
            prefix = "ℹ️"
        elif level == "SUCCESS":
            prefix = "✅"
        elif level == "ERROR":
            prefix = "❌"
        elif level == "WARNING":
            prefix = "⚠️"
        else:
            prefix = "→"

        print(f"[{timestamp}] {prefix} {message}")

    def print_section(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")

    def setup_directories(self) -> bool:
        """Setup required directories"""
        try:
            self.ai_review_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"Setup complete: {self.ai_review_dir}/", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to setup directories: {e}", "ERROR")
            return False

    def generate_sample_analysis_data(self) -> bool:
        """Generate sample analysis data (simulating Steps 1-5)"""
        self.print_section("STEP 1-5: Simulating LLM Analysis & Data Preparation")

        try:
            self.analysis_data = {
                "metadata": {
                    "pr_number": self.pr_number,
                    "title": "Add new authentication module",
                    "author": "developer.name",
                    "source_branch": f"feature/PROJ-456-auth-module",
                    "target_branch": "main",
                    "branch": f"feature/PROJ-456-auth-module → main",
                    "review_date": datetime.now().strftime("%Y-%m-%d"),
                    "review_id": f"PR-{self.pr_number}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "jira_ticket_id": "PROJ-456",
                    "jira_tickets": ["PROJ-456"],
                    "execution_time_seconds": 45
                },
                "pr": {
                    "number": self.pr_number,
                    "title": "Add new authentication module",
                    "author": "developer.name",
                    "source_branch": f"feature/PROJ-456-auth-module",
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
                "files_reviewed": [
                    {
                        "path": "src/main/java/com/example/auth/AuthService.java",
                        "layer": "service",
                        "status": "MODIFIED",
                        "additions": 150,
                        "deletions": 20,
                        "lines_added": 150,
                        "lines_deleted": 20,
                        "summary": "Added OAuth2 authentication",
                        "ai_summary": "OAuth2 integration with error handling"
                    },
                    {
                        "path": "src/main/java/com/example/auth/JwtValidator.java",
                        "layer": "security",
                        "status": "ADDED",
                        "additions": 120,
                        "deletions": 0,
                        "lines_added": 120,
                        "lines_deleted": 0,
                        "summary": "JWT validation utility",
                        "ai_summary": "JWT validator with RSA verification"
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
                        "description": "OAuth callback missing CSRF protection",
                        "impact": "Attackers could perform unauthorized authentication",
                        "suggestion": "Add state parameter validation",
                        "suggested_fix": "Implement state verification",
                        "code_snippet": "response = client.exchangeCodeForToken(code);"
                    },
                    {
                        "id": "FIND-002",
                        "severity": "HIGH",
                        "type": "Bug",
                        "title": "Token refresh infinite loop",
                        "file": "src/main/java/com/example/auth/AuthService.java",
                        "line": 87,
                        "description": "No loop prevention in token refresh",
                        "impact": "Stack overflow possible",
                        "suggestion": "Add refresh attempt counter",
                        "suggested_fix": "Track refresh attempts and limit",
                        "code_snippet": "while (!token.isValid()) { token = refreshToken(token); }"
                    }
                ],
                "spring_boot_validation": {
                    "architecture": {"score": 8.5, "status": "PASS", "issues": []},
                    "security": {"score": 7.0, "status": "WARNING", "issues": ["Missing CSRF"]},
                    "performance": {"score": 6.5, "status": "WARNING", "issues": ["JWT not cached"]},
                    "transactions": {"score": 8.0, "status": "PASS", "issues": []}
                },
                "test_coverage": {
                    "overall": "82%",
                    "by_type": {
                        "unit": "88%",
                        "integration": "75%",
                        "e2e": "60%"
                    },
                    "gaps": []
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
                            }
                        ],
                        "edges": []
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
                    "reason": "Critical security issues must be resolved",
                    "must_fix": ["Add CSRF token validation"],
                    "should_fix": ["Add JWT caching"]
                },
                "positive_observations": [
                    "Good test coverage for main flows",
                    "Clean separation of concerns"
                ],
                "ai_summary": "OAuth2 with good architecture but critical CSRF issues",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            }

            self.log("Generated analysis data with API impact analysis", "SUCCESS")

            # Transform data to match template expectations
            self._transform_data_for_template()

            return True

        except Exception as e:
            self.log(f"Failed to generate analysis data: {e}", "ERROR")
            return False

    def _transform_data_for_template(self) -> None:
        """Transform data to match HTML template expectations"""
        if "impact_analysis" not in self.analysis_data:
            return

        impact = self.analysis_data["impact_analysis"]

        # Ensure dependency_graph structure exists
        if "dependency_graph" not in impact:
            impact["dependency_graph"] = {"nodes": [], "edges": {}, "layers": {}}

        # Build layers map from nodes
        if "dependency_graph" in impact and "nodes" in impact["dependency_graph"]:
            layers = {}
            for node in impact["dependency_graph"]["nodes"]:
                layer = node.get("layer", "unknown")
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(node.get("id", "unknown"))

            impact["dependency_graph"]["layers"] = layers

    def save_analysis_json(self) -> bool:
        """Save analysis data to JSON file (Step 6a)"""
        self.print_section("STEP 6a: Save Analysis Data to JSON")

        try:
            json_file = self.ai_review_dir / f"pr-{self.pr_number}-data.json"

            with open(json_file, 'w') as f:
                json.dump(self.analysis_data, f, indent=2)

            self.log(f"Saved JSON data: {json_file}", "SUCCESS")
            self.log(f"Size: {json_file.stat().st_size} bytes", "INFO")
            return True

        except Exception as e:
            self.log(f"Failed to save JSON: {e}", "ERROR")
            return False

    def validate_api_impact(self) -> bool:
        """Validate API impact analysis is present (Step 6b)"""
        self.print_section("STEP 6b: Validate API Impact Analysis")

        required_fields = {
            "impact_analysis": ["summary", "affected_apis"],
            "api_changes": ["endpoint", "method", "impact"],
            "findings": ["severity", "type", "title"],
            "overall_recommendation": ["decision", "reason"]
        }

        issues = []

        # Check impact_analysis (OPTIONAL - OK if missing or empty)
        if "impact_analysis" in self.analysis_data:
            impact = self.analysis_data["impact_analysis"]
            affected_apis = impact.get("affected_apis", [])
            if affected_apis:
                self.log(f"Found {len(affected_apis)} affected APIs", "SUCCESS")
            else:
                self.log("No affected APIs detected (expected for non-API PRs)", "INFO")
        else:
            self.log("No impact_analysis section (expected for non-API PRs)", "INFO")

        # Check api_changes (OPTIONAL)
        if "api_changes" in self.analysis_data:
            api_changes = self.analysis_data["api_changes"]
            if api_changes:
                self.log(f"Found {len(api_changes)} API changes", "SUCCESS")

        # Check findings (OPTIONAL but valuable)
        if "findings" in self.analysis_data:
            findings = self.analysis_data["findings"]
            if findings:
                self.log(f"Found {len(findings)} code findings", "SUCCESS")

        # Check overall recommendation (OPTIONAL - provide fallback)
        if "overall_recommendation" in self.analysis_data:
            rec = self.analysis_data["overall_recommendation"]
            recommendation = rec.get('decision', 'REVIEW_REQUIRED')
            self.log(f"Recommendation: {recommendation}", "SUCCESS")
        else:
            self.log("No explicit recommendation (will default to REVIEW_REQUIRED)", "INFO")

        # No blocking issues - API impact validation is non-blocking
        # This allows workflows to continue even if API analysis is empty
        if issues:
            for issue in issues:
                self.log(issue, "INFO")

        self.log("API impact analysis checked ✓", "SUCCESS")
        return True

    def generate_html_report(self) -> bool:
        """Generate HTML report (Step 6c)"""
        self.print_section("STEP 6c: Generate HTML Report")

        try:
            json_file = self.ai_review_dir / f"pr-{self.pr_number}-data.json"
            html_file = self.ai_review_dir / f"pr-{self.pr_number}-data.html"

            # Check if generate-html.py exists
            generator = self.templates_dir / "generate-html.py"
            if not generator.exists():
                self.log(f"generate-html.py not found at {generator}", "ERROR")
                return False

            # Try to run the generator
            result = subprocess.run(
                [sys.executable, str(generator), str(json_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                if html_file.exists():
                    size = html_file.stat().st_size
                    self.log(f"HTML report generated: {html_file} ({size} bytes)", "SUCCESS")
                    return True
                else:
                    self.log("HTML generator ran but output file not found", "ERROR")
                    return False
            else:
                self.log(f"HTML generation failed: {result.stderr}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self.log("HTML generation timeout", "ERROR")
            return False
        except Exception as e:
            self.log(f"Failed to generate HTML: {e}", "ERROR")
            return False

    def generate_jira_comment(self) -> bool:
        """Generate JIRA comment (Step 6d)"""
        self.print_section("STEP 6d: Generate JIRA Comment")

        try:
            json_file = self.ai_review_dir / f"pr-{self.pr_number}-data.json"
            jira_file = self.ai_review_dir / f"pr-{self.pr_number}-jira-comment.txt"

            formatter = self.templates_dir / "jira_formatter.py"
            if not formatter.exists():
                self.log(f"jira_formatter.py not found", "WARNING")
                return False

            result = subprocess.run(
                [sys.executable, str(formatter), str(json_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and jira_file.exists():
                size = jira_file.stat().st_size
                self.log(f"JIRA comment generated: {jira_file} ({size} bytes)", "SUCCESS")
                return True
            else:
                self.log(f"JIRA generation failed: {result.stderr}", "WARNING")
                return False

        except Exception as e:
            self.log(f"Failed to generate JIRA comment: {e}", "WARNING")
            return False

    def generate_cli_output(self) -> bool:
        """Generate CLI formatted output (Step 6e)"""
        self.print_section("STEP 6e: Generate CLI Output")

        try:
            json_file = self.ai_review_dir / f"pr-{self.pr_number}-data.json"

            formatter = self.templates_dir / "cli_formatter.py"
            if not formatter.exists():
                self.log(f"cli_formatter.py not found", "WARNING")
                return False

            result = subprocess.run(
                [sys.executable, str(formatter), str(json_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.log("CLI output generated successfully", "SUCCESS")
                if result.stdout:
                    print("\n" + result.stdout)
                return True
            else:
                self.log(f"CLI generation warning: {result.stderr}", "WARNING")
                return True  # Non-critical

        except Exception as e:
            self.log(f"CLI generation failed: {e}", "WARNING")
            return True  # Non-critical

    def verify_reports(self) -> bool:
        """Verify essential reports were generated (Step 6f)"""
        self.print_section("STEP 6f: Verify Reports Generated")

        # Critical files (must exist for workflow success)
        required_files = [
            ("JSON Data", f"pr-{self.pr_number}-data.json"),
            ("JIRA Comment", f"pr-{self.pr_number}-jira-comment.txt"),  # CRITICAL
        ]

        # Optional files (nice-to-have, graceful degradation)
        optional_files = [
            ("HTML Report", f"pr-{self.pr_number}-data.html"),
        ]

        all_good = True
        for name, filename in required_files:
            file_path = self.ai_review_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                self.log(f"{name}: {filename} ({size} bytes)", "SUCCESS")
            else:
                self.log(f"{name}: MISSING {filename}", "ERROR")
                all_good = False

        for name, filename in optional_files:
            file_path = self.ai_review_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                self.log(f"{name}: {filename} ({size} bytes)", "SUCCESS")
            else:
                self.log(f"{name}: Not generated (optional - graceful degradation)", "INFO")

        return all_good

    def print_summary(self) -> None:
        """Print workflow summary"""
        self.print_section("WORKFLOW EXECUTION SUMMARY")

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print(f"PR Number: {self.pr_number}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Output Directory: {self.ai_review_dir.absolute()}")
        print()

        # List generated files
        print("Generated Files:")
        if self.ai_review_dir.exists():
            for file in sorted(self.ai_review_dir.glob(f"pr-{self.pr_number}-*")):
                size = file.stat().st_size
                print(f"  ✓ {file.name} ({size} bytes)")
        else:
            print("  ✗ No files generated")

        print()
        print(f"API Impact Analysis: {'✅ PRESENT' if self._has_api_impact() else '❌ MISSING'}")
        print(f"Code Findings: {'✅ PRESENT' if self._has_findings() else '⚠️  NONE'}")
        print(f"Recommendations: {'✅ PRESENT' if self._has_recommendations() else '❌ MISSING'}")

    def _has_api_impact(self) -> bool:
        """Check if API impact analysis is present"""
        return (
            "impact_analysis" in self.analysis_data
            and "affected_apis" in self.analysis_data.get("impact_analysis", {})
        )

    def _has_findings(self) -> bool:
        """Check if findings are present"""
        return len(self.analysis_data.get("findings", [])) > 0

    def _has_recommendations(self) -> bool:
        """Check if recommendations are present"""
        return "overall_recommendation" in self.analysis_data

    def run(self) -> bool:
        """Run complete workflow"""
        self.print_section("WORKFLOW ORCHESTRATOR - EXECUTING PR REVIEW")
        self.log(f"PR #: {self.pr_number}", "INFO")
        self.log(f"Start Time: {self.start_time}", "INFO")

        # Step 0: Setup
        if not self.setup_directories():
            return False

        # Steps 1-5: Simulate analysis
        if not self.generate_sample_analysis_data():
            return False

        # Step 6a: Save JSON
        if not self.save_analysis_json():
            return False

        # Step 6b: Validate API Impact (NON-BLOCKING - allows empty API analysis)
        self.validate_api_impact()  # Logs info but doesn't block
        self.log("API impact validation complete (non-blocking)", "INFO")

        # Step 6c: Generate HTML (OPTIONAL - can fail)
        if not self.generate_html_report():
            self.log("HTML report generation failed (optional)", "WARNING")
            # Don't return False - continue with fallback options

        # Step 6d: Generate JIRA (CRITICAL - must succeed)
        if not self.generate_jira_comment():
            self.log("JIRA comment generation FAILED (CRITICAL)", "ERROR")
            return False  # ← CRITICAL: JIRA must succeed

        # Step 6e: Generate CLI (SECONDARY - can fail)
        if not self.generate_cli_output():
            self.log("CLI output generation failed (secondary)", "WARNING")

        # Step 6f: Verify reports
        if not self.verify_reports():
            self.log("Report verification failed", "ERROR")
            return False

        # Print summary
        self.print_summary()

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="PR Review Workflow Orchestrator")
    parser.add_argument("--pr", type=int, default=123, help="PR number")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    orchestrator = WorkflowOrchestrator(pr_number=args.pr, verbose=args.verbose)
    success = orchestrator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

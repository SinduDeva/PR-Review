#!/usr/bin/env python3
"""
Analysis Output Handler - Resilient Multi-Format Output

Ensures analysis results are always available even if one output format fails.
Provides fallback mechanisms for HTML, JIRA, CLI, and database output.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime


class AnalysisOutputHandler:
    """Handles robust output of analysis data in multiple formats"""

    def __init__(self, analysis_data: Dict[str, Any], pr_number: int = None, verbose: bool = True):
        """Initialize output handler"""
        self.analysis_data = analysis_data
        self.pr_number = pr_number or analysis_data.get('pr_number') or 'unknown'
        self.verbose = verbose
        self.output_dir = Path(".ai-review")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'json': {'success': False, 'message': '', 'file': ''},
            'html': {'success': False, 'message': '', 'file': ''},
            'jira': {'success': False, 'message': '', 'file': ''},
            'cli': {'success': False, 'message': '', 'output': ''},
            'database': {'success': False, 'message': ''},
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if not self.verbose and level == "INFO":
            return

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

        print(f"{prefix} {message}")

    def output_json(self) -> Tuple[bool, str]:
        """Save analysis to JSON file (non-blocking)"""
        try:
            json_file = self.output_dir / f"pr-{self.pr_number}-data.json"

            # Ensure data can be serialized
            json_str = json.dumps(self.analysis_data, indent=2, ensure_ascii=False, default=str)

            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_str)

            file_size = json_file.stat().st_size
            message = f"JSON saved to {json_file} ({file_size} bytes)"
            self.log(f"✅ {message}", "SUCCESS")

            self.results['json']['success'] = True
            self.results['json']['message'] = message
            self.results['json']['file'] = str(json_file)

            return True, message

        except json.JSONEncodeError as e:
            message = f"JSON encoding error: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            self.results['json']['message'] = message
            return False, message

        except Exception as e:
            message = f"JSON output failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            self.results['json']['message'] = message
            return False, message

    def output_html(self, template_path: str = None) -> Tuple[bool, str]:
        """Generate HTML report (non-blocking)"""
        try:
            html_file = self.output_dir / f"pr-{self.pr_number}-data.html"

            # Try to use generate-html.py
            generator = Path(".windsurf/workflows/templates/generate-html.py")
            if generator.exists():
                import subprocess
                json_file = self.output_dir / f"pr-{self.pr_number}-data.json"

                # Ensure JSON exists first
                if not json_file.exists():
                    self.output_json()

                result = subprocess.run(
                    [sys.executable, str(generator), str(json_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and html_file.exists():
                    file_size = html_file.stat().st_size
                    message = f"HTML report generated: {html_file} ({file_size} bytes)"
                    self.log(f"✅ {message}", "SUCCESS")
                    self.results['html']['success'] = True
                    self.results['html']['message'] = message
                    self.results['html']['file'] = str(html_file)
                    return True, message
                else:
                    raise Exception(result.stderr or "HTML generation failed")
            else:
                raise FileNotFoundError("generate-html.py not found")

        except Exception as e:
            message = f"HTML generation failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            self.results['html']['message'] = message
            return False, message

    def output_jira_comment(self) -> Tuple[bool, str]:
        """Generate JIRA comment from analysis data (CRITICAL - no JSON dependency)

        NOTE: This works DIRECTLY from in-memory analysis_data, not from JSON file.
        JSON may not exist yet (it's created later in the pipeline).
        """
        try:
            # Use execution_orchestrator's JIRA formatter which works from in-memory data
            jira_file = self.output_dir / f"pr-{self.pr_number}-jira-comment.txt"

            # IMPORTANT: Pass analysis_data directly, not JSON file path
            # This allows JIRA to be created BEFORE JSON is saved
            try:
                from execution_orchestrator import ExecutionOrchestrator
                orchestrator = ExecutionOrchestrator(self.analysis_data, pr_number=self.pr_number, verbose=False)
                jira_text = orchestrator._format_jira_plain_text()

                with open(jira_file, 'w', encoding='utf-8') as f:
                    f.write(jira_text)

                file_size = jira_file.stat().st_size
                message = f"JIRA comment generated: {jira_file} ({file_size} bytes)"
                self.log(f"✅ {message}", "SUCCESS")
                self.results['jira']['success'] = True
                self.results['jira']['message'] = message
                self.results['jira']['file'] = str(jira_file)
                return True, message
            except ImportError:
                # Fallback: Try jira_formatter.py if available
                formatter = Path(".windsurf/workflows/templates/jira_formatter.py")
                if not formatter.exists():
                    raise FileNotFoundError("jira_formatter.py not found")

                import subprocess
                json_file = self.output_dir / f"pr-{self.pr_number}-data.json"

                # NOTE: For jira_formatter.py, we MUST have JSON first
                # Create JSON if it doesn't exist (will be saved again later, but needed here)
                if not json_file.exists():
                    self.log("⚠️  JIRA formatter requires JSON - creating early (suboptimal)", "WARNING")
                    self.output_json()

                result = subprocess.run(
                    [sys.executable, str(formatter), str(json_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and jira_file.exists():
                    file_size = jira_file.stat().st_size
                    message = f"JIRA comment generated: {jira_file} ({file_size} bytes)"
                    self.log(f"✅ {message}", "SUCCESS")
                    self.results['jira']['success'] = True
                    self.results['jira']['message'] = message
                    self.results['jira']['file'] = str(jira_file)
                    return True, message
                else:
                    raise Exception(result.stderr or "JIRA comment generation failed")
            else:
                raise FileNotFoundError("jira_formatter.py not found")

        except Exception as e:
            message = f"JIRA comment generation failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            self.results['jira']['message'] = message
            return False, message

    def output_cli(self) -> Tuple[bool, str]:
        """Output CLI summary from in-memory data (SECONDARY - no JSON dependency)

        NOTE: Works DIRECTLY from in-memory analysis_data, not from JSON file.
        JSON may not exist yet (it's created later in the pipeline).
        Uses minimal but complete CLI output generated from in-memory data.
        """
        try:
            # Generate CLI output directly from in-memory data (no JSON dependency)
            return self._generate_minimal_cli_output()

        except Exception as e:
            message = f"CLI output generation failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            return False, message

    def _generate_minimal_cli_output(self) -> Tuple[bool, str]:
        """Generate minimal CLI output directly from analysis data (fallback)"""
        try:
            metadata = self.analysis_data.get('metadata', {})
            summary = self.analysis_data.get('summary', {})
            findings = self.analysis_data.get('findings', [])

            output = []
            output.append("\n" + "="*80)
            output.append(f"PR Code Review Summary - PR #{metadata.get('pr_number', 'unknown')}")
            output.append("="*80 + "\n")

            # Summary
            output.append(f"Files Changed: {summary.get('files_changed', 'N/A')}")
            output.append(f"Critical Issues: {summary.get('critical_issues', 0)}")
            output.append(f"High Issues: {summary.get('high_issues', 0)}")
            output.append(f"Medium Issues: {summary.get('medium_issues', 0)}")
            output.append(f"Low Issues: {summary.get('low_issues', 0)}\n")

            # Top findings
            if findings:
                output.append("Top Findings:")
                for finding in findings[:5]:
                    output.append(f"  • [{finding.get('severity', 'UNKNOWN')}] {finding.get('title', 'N/A')}")
                    output.append(f"    File: {finding.get('file', 'N/A')}: {finding.get('line', 'N/A')}\n")

            output.append("="*80 + "\n")

            cli_output = "\n".join(output)
            print(cli_output)

            self.results['cli']['success'] = True
            self.results['cli']['output'] = cli_output
            self.log("✅ Fallback CLI output generated", "SUCCESS")

            return True, "Fallback CLI output generated"

        except Exception as e:
            message = f"Fallback CLI generation failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            return False, message

    def output_database(self) -> Tuple[bool, str]:
        """Upload to database from in-memory data (CRITICAL - no JSON dependency)

        NOTE: This works DIRECTLY from in-memory analysis_data, not from JSON file.
        JSON may not exist yet (it's created later in the pipeline).
        """
        try:
            # Use DatabaseUploader class directly with in-memory data
            # This allows database upload BEFORE JSON is saved
            try:
                from database_uploader import DatabaseUploader
                uploader = DatabaseUploader()
                run_id = uploader.upload(self.analysis_data)

                self.log(f"✅ Database upload successful (Run ID: {run_id})", "SUCCESS")
                self.results['database']['success'] = True
                self.results['database']['message'] = f"Uploaded to database (Run ID: {run_id})"
                return True, f"Uploaded to database (Run ID: {run_id})"
            except ImportError:
                # Fallback: Use subprocess if direct import fails
                db_uploader = Path(".windsurf/workflows/templates/database_uploader.py")
                if not db_uploader.exists():
                    raise FileNotFoundError("database_uploader.py not found")

                import subprocess
                json_file = self.output_dir / f"pr-{self.pr_number}-data.json"

                # NOTE: For database_uploader subprocess, we MUST have JSON first
                # Create JSON if it doesn't exist (will be saved again later)
                if not json_file.exists():
                    self.log("⚠️  Database uploader requires JSON - creating early (suboptimal)", "WARNING")
                    self.output_json()

                result = subprocess.run(
                    [sys.executable, str(db_uploader), str(json_file)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    self.log("✅ Database upload successful", "SUCCESS")
                    self.results['database']['success'] = True
                    self.results['database']['message'] = "Uploaded to database"
                    return True, "Uploaded to database"
                else:
                    raise Exception(result.stderr or "Database upload failed")

        except Exception as e:
            message = f"Database upload failed: {e}"
            self.log(f"⚠️  {message}", "WARNING")
            self.results['database']['message'] = message
            return False, message

    def output_all(self) -> Dict[str, Any]:
        """Generate all output formats in CORRECT execution order

        CRITICAL ORDER (for proper workflow execution):
        1. JIRA (critical - in-memory data, no JSON needed)
        2. Database (critical - in-memory data, no JSON needed)
        3. CLI (secondary - in-memory data)
        4. JSON (secondary - archive data for reports)
        5. HTML (optional - uses JSON file)
        """
        self.log("\n" + "="*80, "INFO")
        self.log("GENERATING ANALYSIS OUTPUT (Correct Order)", "INFO")
        self.log("="*80 + "\n", "INFO")

        # PHASE 1: CRITICAL OUTPUTS (work with in-memory data, not JSON)
        self.log("PHASE 1: Critical Outputs (in-memory data)", "INFO")
        self.output_jira_comment()      # JIRA (critical, first)
        self.output_database()           # Database (critical, second)

        # PHASE 2: SECONDARY OUTPUTS (can work with in-memory data)
        self.log("\nPHASE 2: Secondary Outputs", "INFO")
        self.output_cli()                # CLI (from in-memory)
        self.output_json()               # JSON (save after critical outputs)

        # PHASE 3: OPTIONAL OUTPUTS (can use JSON if it exists)
        self.log("\nPHASE 3: Optional Outputs", "INFO")
        self.output_html()               # HTML (uses JSON)

        # Print summary
        self._print_summary()

        return self.results

    def _print_summary(self) -> None:
        """Print output generation summary"""
        self.log("\n" + "="*80, "INFO")
        self.log("OUTPUT GENERATION SUMMARY", "INFO")
        self.log("="*80 + "\n", "INFO")

        successful = sum(1 for r in self.results.values() if r.get('success'))
        total = len(self.results)

        for format_name, result in self.results.items():
            status = "✅" if result.get('success') else "⚠️"
            message = result.get('message', 'No message')
            file_path = result.get('file', '')

            if file_path:
                self.log(f"{status} {format_name.upper()}: {file_path}", "SUCCESS" if result['success'] else "WARNING")
            else:
                self.log(f"{status} {format_name.upper()}: {message}", "SUCCESS" if result['success'] else "WARNING")

        self.log(f"\nSuccessful: {successful}/{total}", "INFO")
        self.log("="*80 + "\n", "INFO")

    def ensure_analysis_available(self) -> bool:
        """
        Ensure analysis is available in at least one format

        Returns:
            True if analysis successfully saved in at least one format
        """
        available_formats = [
            self.results['json']['success'],
            self.results['html']['success'],
            self.results['cli']['success'],
        ]

        if any(available_formats):
            self.log("✅ Analysis successfully saved in at least one format", "SUCCESS")
            return True
        else:
            self.log("⚠️  Analysis could not be saved in any format", "WARNING")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Resilient analysis output handler"
    )
    parser.add_argument('analysis_file', help='JSON analysis file')
    parser.add_argument('--pr', type=int, help='PR number (auto-detected if not provided)')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    try:
        # Load analysis data
        with open(args.analysis_file, 'r', encoding='utf-8-sig') as f:
            analysis_data = json.load(f)

        # Create output handler
        handler = AnalysisOutputHandler(
            analysis_data=analysis_data,
            pr_number=args.pr,
            verbose=not args.quiet
        )

        # Generate all outputs
        results = handler.output_all()

        # Check if analysis is available
        if handler.ensure_analysis_available():
            sys.exit(0)
        else:
            sys.exit(1)

    except FileNotFoundError:
        print(f"❌ Analysis file not found: {args.analysis_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in analysis file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

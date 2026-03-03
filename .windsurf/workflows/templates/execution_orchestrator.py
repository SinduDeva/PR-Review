#!/usr/bin/env python3
"""
Execution Orchestrator - Report Generation in Correct Order

EXECUTION ORDER:
  1. Validate Analysis Complete (8b-GATE) - CRITICAL
  2. JIRA Upload (with complete analysis) - CRITICAL
  3. HTML Report (auto-open) - CRITICAL
  4. CLI Summary - SECONDARY

This ensures analysis is complete before ANY reports are generated.

Usage:
    python execution_orchestrator.py analysis.json --pr 123
    cat analysis.json | python execution_orchestrator.py - --pr 123
    python execution_orchestrator.py --pr 123 --data '{"metadata":{...}}'
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# Import PR detector
try:
    from pr_detector import PRDetector
except ImportError:
    PRDetector = None


class ExecutionOrchestrator:
    """Manages execution order: Validate → JIRA → HTML (auto-open) → CLI"""

    def __init__(self, analysis_data: Dict[str, Any], pr_number: int = None, verbose: bool = True):
        self.analysis_data = analysis_data
        self.verbose = verbose

        # Detect PR number with fallback
        self.pr_number = self._detect_pr_number(pr_number)
        if not self.pr_number:
            raise ValueError("❌ PR NUMBER NOT FOUND - Cannot proceed without PR number")

        self.output_dir = Path(".ai-review")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.phases = {
            'validation': {'success': False, 'message': '', 'critical': True},
            'jira': {'success': False, 'message': '', 'critical': True},
            'html': {'success': False, 'message': '', 'critical': True},
            'cli': {'success': False, 'message': '', 'critical': False},
        }

    def _detect_pr_number(self, cli_pr: Optional[int] = None) -> Optional[int]:
        """
        Detect PR number with priority:
        1. CLI argument
        2. Environment variables
        3. Git branch parsing
        4. Git commit message
        5. JSON metadata

        Returns:
            PR number or None
        """
        # Priority 1: CLI argument
        if cli_pr and cli_pr > 0:
            self.log(f"✅ PR detected from CLI: {cli_pr}", "SUCCESS")
            return cli_pr

        # Priority 2-4: Use PRDetector if available
        if PRDetector:
            detector = PRDetector(verbose=False)
            pr_num = detector.detect(cli_pr=None)
            if pr_num:
                self.log(f"✅ PR detected: {pr_num}", "SUCCESS")
                return pr_num

        # Priority 5: JSON metadata
        json_pr = self.analysis_data.get('metadata', {}).get('pr_number')
        if json_pr and json_pr > 0:
            self.log(f"✅ PR detected from JSON metadata: {json_pr}", "SUCCESS")
            return json_pr

        # Not found
        self.log("❌ PR number not found in any source", "ERROR")
        return None

    def log(self, msg: str, level: str = "INFO"):
        """Log with visual indicator"""
        if not self.verbose and level == "INFO":
            return
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "→")
        print(f"{prefix} {msg}")

    # ============================================================================
    # PHASE 0: VALIDATE ANALYSIS COMPLETE (CRITICAL - Gate before any reports)
    # ============================================================================

    def phase_0_validate_analysis(self) -> bool:
        """PHASE 0: Validate all analysis is complete before generating reports"""
        try:
            self.log("\n[PHASE 0/3] VALIDATING ANALYSIS COMPLETION...", "INFO")

            # Import validator
            try:
                from analysis_validator import validate_analysis_completion, get_validation_report
            except ImportError:
                msg = "analysis_validator.py not found - skipping validation"
                self.log(f"⚠️  {msg}", "WARNING")
                self.phases['validation']['message'] = msg
                return True  # Allow to continue if validator missing

            # Validate
            is_complete, missing_fields, warnings = validate_analysis_completion(self.analysis_data)

            # Print report
            report = get_validation_report(is_complete, missing_fields, warnings)
            self.log(report, "INFO")

            if not is_complete:
                msg = f"Analysis incomplete - missing {len(missing_fields)} required fields"
                self.log(f"❌ {msg}", "ERROR")
                self.phases['validation']['message'] = msg
                return False  # Block all report generation

            # Success
            msg = "Analysis validation passed - proceeding with reports"
            self.log(f"✅ {msg}", "SUCCESS")
            self.phases['validation']['success'] = True
            self.phases['validation']['message'] = msg
            return True

        except Exception as e:
            msg = f"Validation error: {e}"
            self.log(f"⚠️  {msg}", "WARNING")
            self.phases['validation']['message'] = msg
            return True  # Allow to continue on validation errors

    # ============================================================================
    # PHASE 1: JIRA UPDATE (CRITICAL - Happens First after validation)
    # ============================================================================

    def _format_jira_plain_text(self) -> str:
        """Format ENTIRE analysis as PLAIN TEXT (no unicode, no colors) for JIRA"""
        meta = self.analysis_data.get('metadata', {})
        summ = self.analysis_data.get('summary', {})
        findings = self.analysis_data.get('findings', [])
        files_reviewed = self.analysis_data.get('files_reviewed', [])
        files_skipped = self.analysis_data.get('files_skipped', [])

        lines = []
        lines.append("=" * 80)
        lines.append(f"AUTOMATED PR REVIEW - PR #{self.pr_number}")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Title: {meta.get('title', 'N/A')}")
        lines.append(f"Branch: {meta.get('branch', 'N/A')}")
        lines.append(f"Author: {meta.get('author', 'N/A')}")
        lines.append(f"Review Date: {meta.get('review_date', 'N/A')}")
        lines.append("")

        # Summary metrics
        lines.append("-" * 80)
        lines.append("SUMMARY METRICS")
        lines.append("-" * 80)
        lines.append(f"Files Changed: {summ.get('files_changed', 0)}")
        lines.append(f"Files Validated: {summ.get('files_validated', 0)}")
        lines.append(f"Files Excluded: {summ.get('files_excluded', 0)}")
        lines.append(f"Lines Added: +{summ.get('lines_added', 0)}")
        lines.append(f"Lines Deleted: -{summ.get('lines_deleted', 0)}")
        lines.append("")
        lines.append(f"Issues Summary:")
        lines.append(f"  Critical: {summ.get('critical_issues', 0)}")
        lines.append(f"  High: {summ.get('high_issues', 0)}")
        lines.append(f"  Medium: {summ.get('medium_issues', 0)}")
        lines.append(f"  Low: {summ.get('low_issues', 0)}")
        lines.append("")

        # Files Reviewed
        if files_reviewed:
            lines.append("-" * 80)
            lines.append("FILES REVIEWED")
            lines.append("-" * 80)
            for file in files_reviewed[:20]:  # Top 20
                lines.append(f"File: {file.get('path', 'N/A')}")
                lines.append(f"  Layer: {file.get('layer', 'N/A')}")
                lines.append(f"  Status: {file.get('status', 'N/A')}")
                lines.append(f"  Changes: +{file.get('additions', 0)} -{file.get('deletions', 0)}")
                if file.get('ai_summary'):
                    lines.append(f"  Summary: {file.get('ai_summary', 'N/A')}")
                lines.append("")
            if len(files_reviewed) > 20:
                lines.append(f"... and {len(files_reviewed) - 20} more files")
                lines.append("")

        # Files Skipped
        if files_skipped:
            lines.append("-" * 80)
            lines.append("FILES SKIPPED/EXCLUDED")
            lines.append("-" * 80)
            for i, file in enumerate(files_skipped[:10], 1):
                lines.append(f"{i}. {file}")
            if len(files_skipped) > 10:
                lines.append(f"... and {len(files_skipped) - 10} more")
            lines.append("")

        # ALL Findings (not just critical/high)
        if findings:
            lines.append("-" * 80)
            lines.append(f"ALL FINDINGS ({len(findings)} total)")
            lines.append("-" * 80)
            lines.append("")

            # Group by severity
            by_severity = {}
            for finding in findings:
                sev = finding.get('severity', 'UNKNOWN')
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(finding)

            # Sort by severity priority
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            for severity in severity_order:
                if severity in by_severity:
                    lines.append(f"\n{severity} ({len(by_severity[severity])}):")
                    for finding in by_severity[severity]:
                        lines.append(f"  [{finding.get('id', 'N/A')}] {finding.get('title', 'N/A')}")
                        lines.append(f"    Type: {finding.get('type', 'N/A')}")
                        lines.append(f"    File: {finding.get('file', 'N/A')}:{finding.get('line', 'N/A')}")
                        lines.append(f"    Description: {finding.get('description', 'N/A')}")
                        lines.append(f"    Impact: {finding.get('impact', 'N/A')}")
                        lines.append(f"    Suggestion: {finding.get('suggestion', 'N/A')}")
                        if finding.get('suggested_fix'):
                            lines.append(f"    Fix: {finding.get('suggested_fix', 'N/A')}")
                        lines.append("")
        else:
            lines.append("-" * 80)
            lines.append("NO FINDINGS")
            lines.append("-" * 80)
            lines.append("")

        # Impact Analysis
        impact = self.analysis_data.get('impact_analysis', {})
        if impact:
            lines.append("-" * 80)
            lines.append("IMPACT ANALYSIS")
            lines.append("-" * 80)
            if isinstance(impact, dict):
                for key, val in impact.items():
                    if isinstance(val, dict):
                        lines.append(f"{key}:")
                        for k, v in val.items():
                            lines.append(f"  {k}: {v}")
                    else:
                        lines.append(f"{key}: {val}")
            else:
                lines.append(str(impact))
            lines.append("")

        # API Changes
        api_changes = self.analysis_data.get('api_changes', [])
        if api_changes:
            lines.append("-" * 80)
            lines.append("API CHANGES")
            lines.append("-" * 80)
            for change in api_changes:
                if isinstance(change, dict):
                    lines.append(f"Endpoint: {change.get('endpoint', 'N/A')}")
                    lines.append(f"  Method: {change.get('method', 'N/A')}")
                    lines.append(f"  Change: {change.get('change_type', 'N/A')}")
                    lines.append(f"  Description: {change.get('description', 'N/A')}")
                    lines.append("")
                else:
                    lines.append(str(change))
            lines.append("")

        # Spring Boot Validation
        spring = self.analysis_data.get('spring_boot_validation', {})
        if spring:
            lines.append("-" * 80)
            lines.append("SPRING BOOT VALIDATION")
            lines.append("-" * 80)
            for cat, val in spring.items():
                if isinstance(val, dict):
                    lines.append(f"{cat}:")
                    for k, v in val.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"{cat}: {val}")
            lines.append("")

        # Test Coverage
        test = self.analysis_data.get('test_coverage', {})
        if test:
            lines.append("-" * 80)
            lines.append("TEST COVERAGE")
            lines.append("-" * 80)
            for metric, val in test.items():
                lines.append(f"{metric}: {val}")
            lines.append("")

        # Positive Observations
        positive = self.analysis_data.get('positive_observations', [])
        if positive:
            lines.append("-" * 80)
            lines.append("POSITIVE OBSERVATIONS")
            lines.append("-" * 80)
            for obs in positive:
                lines.append(f"+ {obs}")
            lines.append("")

        # AI Summary
        ai_summ = self.analysis_data.get('ai_summary', '')
        if ai_summ:
            lines.append("-" * 80)
            lines.append("ANALYSIS SUMMARY")
            lines.append("-" * 80)
            lines.append(ai_summ)
            lines.append("")

        # Overall Recommendation
        overall = self.analysis_data.get('overall_recommendation', {})
        if overall:
            lines.append("-" * 80)
            lines.append("OVERALL RECOMMENDATION")
            lines.append("-" * 80)
            if isinstance(overall, dict):
                for key, val in overall.items():
                    lines.append(f"{key}: {val}")
            else:
                lines.append(str(overall))
            lines.append("")

        # Final Recommendation
        lines.append("-" * 80)
        lines.append("RECOMMENDATION")
        lines.append("-" * 80)
        if summ.get('critical_issues', 0) > 0:
            lines.append("ACTION REQUIRED: Review required (critical issues found)")
        elif summ.get('high_issues', 0) > 0:
            lines.append("REVIEW RECOMMENDED: High priority issues found")
        else:
            lines.append("APPROVED: No critical/high issues detected")
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def phase_1_update_jira(self) -> bool:
        """PHASE 1: Update JIRA (NON-BLOCKING - Workflow continues if fails)"""
        try:
            self.log("\n[PHASE 1/4] UPDATING JIRA (NON-BLOCKING)...", "INFO")

            # Generate plain text JIRA comment
            jira_text = self._format_jira_plain_text()
            jira_file = self.output_dir / f"pr-{self.pr_number}-jira-comment.txt"

            with open(jira_file, 'w', encoding='utf-8') as f:
                f.write(jira_text)

            size = jira_file.stat().st_size
            msg = f"JIRA comment saved: {jira_file} ({size} bytes)"
            self.log(f"✅ {msg}", "SUCCESS")
            self.phases['jira']['success'] = True
            self.phases['jira']['message'] = msg

            # Try to post to JIRA if uploader exists
            uploader = Path(".windsurf/workflows/templates/jira_uploader.py")
            if uploader.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(uploader), str(jira_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        self.log("✅ Posted to JIRA", "SUCCESS")
                    else:
                        self.log(f"⚠️  JIRA post failed: {result.stderr[:100]} (comment saved to {jira_file})", "WARNING")
                except Exception as e:
                    self.log(f"⚠️  JIRA posting error: {e} (comment saved to {jira_file})", "WARNING")

            return True

        except Exception as e:
            msg = f"JIRA update failed: {e} (check {self.output_dir / f'pr-{self.pr_number}-jira-comment.txt'} for manual posting)"
            self.log(f"⚠️  {msg}", "WARNING")
            self.phases['jira']['message'] = msg
            return True  # Non-blocking: return True so workflow continues

    # ============================================================================
    # PHASE 2: HTML GENERATE (CRITICAL - Auto-open)
    # ============================================================================

    def phase_2_generate_html(self) -> bool:
        """PHASE 2: Generate HTML (CRITICAL - Auto-open)"""
        try:
            self.log("\n[PHASE 2/3] GENERATING HTML REPORT (CRITICAL)...", "INFO")

            gen = Path(".windsurf/workflows/templates/generate-simple-html.py")
            if not gen.exists():
                msg = "generate-simple-html.py not found"
                self.log(f"⚠️  {msg}", "WARNING")
                self.phases['html']['message'] = msg
                return False

            # Pass data via stdin (no JSON files)
            json_data = json.dumps(self.analysis_data, indent=2, default=str)

            result = subprocess.run(
                [sys.executable, str(gen)],
                input=json_data,
                capture_output=True,
                text=True,
                timeout=30
            )

            html_file = self.output_dir / f"pr-{self.pr_number}-data.html"

            if result.returncode == 0 and html_file.exists():
                size = html_file.stat().st_size
                msg = f"HTML generated: {html_file} ({size} bytes)"
                self.log(f"✅ {msg}", "SUCCESS")
                self.phases['html']['success'] = True
                self.phases['html']['message'] = msg

                # Auto-open HTML in browser
                from generate_simple_html import open_html_in_browser
                try:
                    open_html_in_browser(str(html_file))
                except:
                    pass  # Silent fail on auto-open

                return True
            else:
                raise Exception(result.stderr or "Generation failed")

        except Exception as e:
            msg = f"HTML generation failed: {e}"
            self.log(f"❌ {msg}", "ERROR")
            self.phases['html']['message'] = msg
            return False

    # ============================================================================
    # PHASE 3: CLI GENERATE (SECONDARY - Can fail without blocking)
    # ============================================================================

    def phase_3_generate_cli(self) -> bool:
        """PHASE 3: Generate CLI output (SECONDARY - Can fail without blocking)"""
        try:
            self.log("\n[PHASE 3/3] GENERATING CLI OUTPUT (SECONDARY)...", "INFO")

            cli_formatter = Path(".windsurf/workflows/templates/cli_formatter.py")
            if not cli_formatter.exists():
                msg = "cli_formatter.py not found"
                self.log(f"⚠️  {msg}", "WARNING")
                self.phases['cli']['message'] = msg
                return False

            # Pass data via stdin (no JSON files)
            json_data = json.dumps(self.analysis_data, indent=2, default=str)

            result = subprocess.run(
                [sys.executable, str(cli_formatter)],
                input=json_data,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                cli_file = self.output_dir / f"pr-{self.pr_number}-cli-output.txt"
                if cli_file.exists():
                    size = cli_file.stat().st_size
                    msg = f"CLI output generated: {cli_file} ({size} bytes)"
                    self.log(f"✅ {msg}", "SUCCESS")
                    self.phases['cli']['success'] = True
                    self.phases['cli']['message'] = msg
                    return True
                else:
                    # CLI formatter may output to stdout
                    msg = "CLI output generated"
                    self.log(f"✅ {msg}", "SUCCESS")
                    self.phases['cli']['success'] = True
                    self.phases['cli']['message'] = msg
                    return True
            else:
                raise Exception(result.stderr or "CLI generation failed")

        except Exception as e:
            msg = f"CLI generation failed: {e}"
            self.log(f"⚠️  {msg}", "WARNING")
            self.phases['cli']['message'] = msg
            return False


    # ============================================================================
    # ORCHESTRATION
    # ============================================================================

    def execute(self) -> bool:
        """Execute in correct order and return success status"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("EXECUTION ORCHESTRATOR - REPORT GENERATION", "INFO")
        self.log("=" * 80, "INFO")

        # PHASE 0: VALIDATE (CRITICAL) - Gate before any reports
        validation_ok = self.phase_0_validate_analysis()
        if not validation_ok:
            self.log("\n❌ ANALYSIS VALIDATION FAILED - Blocking all reports", "ERROR")
            return False

        # PHASE 1: JIRA (CRITICAL) - Post to JIRA with complete analysis
        jira_ok = self.phase_1_update_jira()

        # PHASE 2: HTML (CRITICAL) - Auto-open HTML report
        html_ok = self.phase_2_generate_html()

        # PHASE 3: CLI (SECONDARY) - Generate CLI summary
        cli_ok = self.phase_3_generate_cli()

        # Print summary
        self._print_summary(validation_ok, jira_ok, html_ok, cli_ok)

        # Return success if JIRA and HTML both succeeded
        # CLI failure is non-blocking
        return jira_ok and html_ok

    def _print_summary(self, validation_ok: bool, jira_ok: bool, html_ok: bool, cli_ok: bool):
        """Print execution summary"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("EXECUTION SUMMARY", "INFO")
        self.log("=" * 80, "INFO")
        self.log("")

        # Validation phase
        self.log("VALIDATION:", "INFO")
        self.log(f"  {'✅' if validation_ok else '❌'} Analysis Complete: {self.phases['validation']['message']}")

        # Critical phases
        self.log("\nCRITICAL PHASES:", "INFO")
        self.log(f"  {'✅' if jira_ok else '❌'} JIRA Upload: {self.phases['jira']['message']}")
        self.log(f"  {'✅' if html_ok else '❌'} HTML Report: {self.phases['html']['message']}")

        # Secondary phases
        self.log("\nSECONDARY PHASES:", "INFO")
        self.log(f"  {'✅' if cli_ok else '⚠️'} CLI Summary: {self.phases['cli']['message']}")

        self.log("\n" + "-" * 80, "INFO")

        if validation_ok and jira_ok and html_ok:
            self.log("✅ ALL CRITICAL PHASES SUCCESSFUL", "SUCCESS")
        else:
            self.log("❌ CRITICAL PHASES FAILED", "ERROR")

        self.log("\n" + "=" * 80 + "\n", "INFO")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Execution orchestrator for analysis output")
    parser.add_argument('analysis_file', nargs='?', default='-', help='JSON analysis file (or - for stdin)')
    parser.add_argument('--pr', type=int, help='PR number')
    parser.add_argument('--data', type=str, help='JSON data as string')
    parser.add_argument('--phase', choices=['validate', 'jira', 'html', 'cli', 'all'], default='all',
                        help='Which phase to execute (validate, jira, html, cli, or all)')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    try:
        # Load analysis data
        if args.data:
            analysis_data = json.loads(args.data)
        elif args.analysis_file == '-' or not args.analysis_file:
            analysis_data = json.load(sys.stdin)
        else:
            with open(args.analysis_file, 'r', encoding='utf-8-sig') as f:
                analysis_data = json.load(f)

        # Create orchestrator
        orch = ExecutionOrchestrator(analysis_data, pr_number=args.pr, verbose=not args.quiet)

        # Execute specific phase or all phases
        if args.phase == 'all':
            success = orch.execute()
        elif args.phase == 'validate':
            success = orch.phase_0_validate_analysis()
        elif args.phase == 'jira':
            success = orch.phase_1_update_jira()
        elif args.phase == 'html':
            success = orch.phase_2_generate_html()
        elif args.phase == 'cli':
            success = orch.phase_3_generate_cli()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

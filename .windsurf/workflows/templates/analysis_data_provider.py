#!/usr/bin/env python3
"""
Analysis Data Provider - In-Memory Resilient Analysis Management

Manages analysis data throughout workflow execution, ensuring complete
analysis is always available even if serialization/storage fails.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


@dataclass
class Finding:
    """Code finding/issue"""
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    type: str
    title: str
    file: str
    line: int
    description: str
    impact: str
    suggestion: str
    suggested_fix: str = ""
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileSummary:
    """Summary of reviewed file"""
    path: str
    layer: str
    status: str  # ADDED, MODIFIED, DELETED
    additions: int = 0
    deletions: int = 0
    summary: str = ""
    ai_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisMetadata:
    """Metadata for analysis execution"""
    pr_number: int
    title: str = ""
    author: str = ""
    source_branch: str = ""
    target_branch: str = ""
    branch: str = ""
    review_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    review_id: str = field(default_factory=lambda: f"PR-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    jira_ticket_id: Optional[str] = None
    jira_tickets: List[str] = field(default_factory=list)
    execution_time_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisSummary:
    """Summary metrics for analysis"""
    files_changed: int = 0
    files_validated: int = 0
    files_excluded: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    bugs_detected: int = 0
    test_coverage: str = "N/A"
    test_coverage_overall: str = "N/A"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnalysisDataProvider:
    """Manages analysis data throughout workflow execution"""

    def __init__(self):
        """Initialize analysis data container"""
        self.metadata: Optional[AnalysisMetadata] = None
        self.summary: AnalysisSummary = AnalysisSummary()
        self.findings: List[Finding] = []
        self.files_reviewed: List[FileSummary] = []
        self.files_skipped: List[str] = []

        # Optional analysis sections
        self.spring_boot_validation: Dict[str, Any] = {}
        self.test_coverage: Dict[str, Any] = {}
        self.impact_analysis: Dict[str, Any] = {}
        self.api_changes: List[Dict[str, Any]] = []
        self.overall_recommendation: Dict[str, Any] = {}
        self.positive_observations: List[str] = []
        self.ai_summary: str = ""

        # Execution tracking
        self.generation_start: datetime = datetime.now()

    def set_metadata(self, **kwargs) -> None:
        """Set metadata fields"""
        if self.metadata is None:
            self.metadata = AnalysisMetadata(**{k: v for k, v in kwargs.items() if k in AnalysisMetadata.__dataclass_fields__})
        else:
            for key, value in kwargs.items():
                if hasattr(self.metadata, key):
                    setattr(self.metadata, key, value)

    def add_finding(self, finding: Finding) -> None:
        """Add a code finding"""
        self.findings.append(finding)

        # Update summary counts
        if finding.severity == "CRITICAL":
            self.summary.critical_issues += 1
        elif finding.severity == "HIGH":
            self.summary.high_issues += 1
        elif finding.severity == "MEDIUM":
            self.summary.medium_issues += 1
        elif finding.severity == "LOW":
            self.summary.low_issues += 1

    def add_findings(self, findings: List[Finding]) -> None:
        """Add multiple findings"""
        for finding in findings:
            self.add_finding(finding)

    def add_file_reviewed(self, file_summary: FileSummary) -> None:
        """Add reviewed file"""
        self.files_reviewed.append(file_summary)
        self.summary.files_validated += 1
        self.summary.lines_added += file_summary.additions
        self.summary.lines_deleted += file_summary.deletions

    def add_files_reviewed(self, files: List[FileSummary]) -> None:
        """Add multiple reviewed files"""
        for file in files:
            self.add_file_reviewed(file)

    def skip_file(self, file_path: str) -> None:
        """Mark file as skipped"""
        self.files_skipped.append(file_path)
        self.summary.files_excluded += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "metadata": self.metadata.to_dict() if self.metadata else {},
            "summary": self.summary.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "files_reviewed": [f.to_dict() for f in self.files_reviewed],
            "files_skipped": self.files_skipped,
        }

        # Add optional sections if populated
        if self.spring_boot_validation:
            result["spring_boot_validation"] = self.spring_boot_validation
        if self.test_coverage:
            result["test_coverage"] = self.test_coverage
        if self.impact_analysis:
            result["impact_analysis"] = self.impact_analysis
        if self.api_changes:
            result["api_changes"] = self.api_changes
        if self.overall_recommendation:
            result["overall_recommendation"] = self.overall_recommendation
        if self.positive_observations:
            result["positive_observations"] = self.positive_observations
        if self.ai_summary:
            result["ai_summary"] = self.ai_summary

        # Add execution metadata
        result["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        result["generation_duration_seconds"] = int((datetime.now() - self.generation_start).total_seconds())

        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, default=str)

    def validate(self) -> tuple[bool, List[str], List[str]]:
        """
        Validate analysis data completeness

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check required fields
        if self.metadata is None:
            errors.append("Metadata not set")
        elif self.metadata.pr_number is None:
            errors.append("PR number not set in metadata")

        if self.summary.files_validated == 0:
            warnings.append("No files were validated")

        if len(self.findings) == 0:
            warnings.append("No findings detected")

        # Check for data consistency
        total_issues = (
            self.summary.critical_issues +
            self.summary.high_issues +
            self.summary.medium_issues +
            self.summary.low_issues
        )

        if total_issues != len(self.findings):
            warnings.append(
                f"Issue count mismatch: summary has {total_issues} but {len(self.findings)} findings exist"
            )

        return len(errors) == 0, errors, warnings

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_findings": len(self.findings),
            "critical": self.summary.critical_issues,
            "high": self.summary.high_issues,
            "medium": self.summary.medium_issues,
            "low": self.summary.low_issues,
            "files_reviewed": self.summary.files_validated,
            "lines_added": self.summary.lines_added,
            "lines_deleted": self.summary.lines_deleted,
        }

    def get_recommendations_summary(self) -> str:
        """Get human-readable recommendations"""
        if not self.findings:
            return "✅ No issues found"

        critical_count = self.summary.critical_issues
        high_count = self.summary.high_issues

        if critical_count > 0:
            return f"❌ REQUEST CHANGES: {critical_count} critical and {high_count} high priority issues found"
        elif high_count > 0:
            return f"⚠️  REVIEW COMMENTS: {high_count} high priority issues found"
        else:
            return "✅ APPROVE: Only low/medium priority issues found"

    def print_summary(self) -> None:
        """Print analysis summary to stdout"""
        if self.metadata is None:
            print("No analysis data available")
            return

        print("\n" + "="*80)
        print(f"Analysis Summary - PR #{self.metadata.pr_number}")
        print("="*80 + "\n")

        summary_stats = self.get_summary()
        print(f"Files Reviewed: {summary_stats['files_reviewed']}")
        print(f"Total Findings: {summary_stats['total_findings']}")
        print(f"  • Critical: {summary_stats['critical']}")
        print(f"  • High: {summary_stats['high']}")
        print(f"  • Medium: {summary_stats['medium']}")
        print(f"  • Low: {summary_stats['low']}\n")

        print(f"Lines Changed: +{summary_stats['lines_added']} -{summary_stats['lines_deleted']}\n")
        print(f"Recommendation: {self.get_recommendations_summary()}\n")
        print("="*80 + "\n")


def main():
    """Example usage and testing"""
    # Create provider
    provider = AnalysisDataProvider()

    # Set metadata
    provider.set_metadata(
        pr_number=123,
        title="Add authentication module",
        author="developer@example.com",
        source_branch="feature/auth",
        target_branch="main"
    )

    # Add files
    provider.add_files_reviewed([
        FileSummary(
            path="src/auth/service.py",
            layer="service",
            status="ADDED",
            additions=150,
            deletions=0,
            summary="Authentication service"
        ),
    ])

    # Add findings
    provider.add_findings([
        Finding(
            id="FIND-001",
            severity="CRITICAL",
            type="Security",
            title="Missing CSRF token validation",
            file="src/auth/service.py",
            line=45,
            description="OAuth callback missing CSRF protection",
            impact="Attackers could perform unauthorized authentication",
            suggestion="Add state parameter validation",
            suggested_fix="Implement state verification"
        ),
    ])

    # Validate and print
    is_valid, errors, warnings = provider.validate()
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    if warnings:
        print(f"Warnings: {warnings}")

    # Print summary
    provider.print_summary()

    # Convert to JSON
    analysis_json = provider.to_json()
    print("\nJSON Output:")
    print(analysis_json)


if __name__ == "__main__":
    main()

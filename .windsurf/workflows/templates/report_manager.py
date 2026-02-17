#!/usr/bin/env python3
"""
Report Manager - Handles archiving and indexing of PR review reports

Features:
- Archives previous runs to numbered subdirectories (pr-123-run-1/, pr-123-run-2/)
- Keeps latest reports in .ai-review/ root for easy access
- Maintains index.json tracking all runs
- Enables report history tracking across multiple executions
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


class ReportManager:
    """Manages report organization and archiving"""

    def __init__(self, pr_number, base_dir=".ai-review"):
        """Initialize report manager for a specific PR"""
        self.pr_number = pr_number
        self.base_dir = base_dir
        self.pr_dir = os.path.join(base_dir, f"pr-{pr_number}")
        self.index_file = os.path.join(base_dir, "index.json")

        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)

    def archive_previous_run(self):
        """Archive the previous run (if any) to a numbered subdirectory"""
        # Get the next run number
        run_number = self._get_next_run_number()

        if run_number <= 1:
            # First run, nothing to archive
            return

        # Create archive directory for previous run
        prev_run_number = run_number - 1
        archive_dir = os.path.join(self.base_dir, f"pr-{self.pr_number}-run-{prev_run_number}")
        os.makedirs(archive_dir, exist_ok=True)

        # Files to archive
        files_to_archive = [
            f"pr-{self.pr_number}-data.json",
            f"pr-{self.pr_number}-data.html",
            f"pr-{self.pr_number}-jira-comment.txt",
        ]

        # Move files to archive directory
        for filename in files_to_archive:
            src = os.path.join(self.base_dir, filename)
            dst = os.path.join(archive_dir, filename.replace(f"pr-{self.pr_number}-", ""))

            if os.path.exists(src):
                shutil.move(src, dst)
                print(f"✅ Archived: {filename} → run-{prev_run_number}/")

    def _get_next_run_number(self):
        """Get the next run number by checking existing run directories"""
        max_run = 0
        for item in os.listdir(self.base_dir):
            if item.startswith(f"pr-{self.pr_number}-run-"):
                try:
                    run_num = int(item.split("-run-")[1])
                    max_run = max(max_run, run_num)
                except (ValueError, IndexError):
                    continue

        return max_run + 1

    def get_current_run_number(self):
        """Get the current run number"""
        return self._get_next_run_number()

    def update_index(self, json_data):
        """Update the master index.json file with current run metadata"""
        # Load existing index or create new
        index = {}
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                index = {}

        # Ensure pr_number entry exists
        if f"pr-{self.pr_number}" not in index:
            index[f"pr-{self.pr_number}"] = {
                "pr_number": self.pr_number,
                "runs": []
            }

        # Add current run info
        run_number = self.get_current_run_number()
        run_entry = {
            "run_number": run_number,
            "timestamp": datetime.now().isoformat(),
            "status": json_data.get("execution_status", {}).get("overall_status", "unknown"),
            "files_changed": json_data.get("files_changed_count", 0),
            "findings_count": len(json_data.get("findings", [])),
            "critical_issues": len([f for f in json_data.get("findings", []) if f.get("severity") == "CRITICAL"]),
            "high_issues": len([f for f in json_data.get("findings", []) if f.get("severity") == "HIGH"]),
            "jira_ticket_id": json_data.get("jira_ticket_id"),
        }

        # Update index with current run
        index[f"pr-{self.pr_number}"]["runs"] = [run_entry] + index[f"pr-{self.pr_number}"]["runs"]
        index[f"pr-{self.pr_number}"]["latest_run"] = run_number
        index[f"pr-{self.pr_number}"]["last_update"] = datetime.now().isoformat()

        # Save updated index
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)

        print(f"✅ Index updated: {self.index_file}")
        return index

    def get_run_history(self):
        """Get the run history for this PR"""
        if not os.path.exists(self.index_file):
            return []

        try:
            with open(self.index_file, 'r') as f:
                index = json.load(f)
                return index.get(f"pr-{self.pr_number}", {}).get("runs", [])
        except (json.JSONDecodeError, IOError):
            return []

    def print_run_summary(self):
        """Print summary of current run"""
        run_number = self.get_current_run_number()
        print(f"\n{'='*70}")
        print(f"📊 REPORT SUMMARY")
        print(f"{'='*70}")
        print(f"  PR Number: #{self.pr_number}")
        print(f"  Run Number: #{run_number}")
        print(f"  Reports Location: .ai-review/")
        print(f"  Archive Location: .ai-review/pr-{self.pr_number}-run-{run_number-1}/ (if re-run)")
        print(f"  Master Index: .ai-review/index.json")
        print(f"{'='*70}\n")


def archive_reports_for_rerun(pr_number):
    """Convenience function to archive reports before a re-run"""
    manager = ReportManager(pr_number)
    manager.archive_previous_run()
    return manager


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python report_manager.py <pr_number> [json_file]")
        sys.exit(1)

    pr_number = sys.argv[1]
    manager = ReportManager(pr_number)

    if len(sys.argv) > 2:
        # Update index with JSON data
        json_file = sys.argv[2]
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            manager.update_index(json_data)
            manager.print_run_summary()
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        # Just archive previous run
        manager.archive_previous_run()
        print(f"✅ Archive complete for PR #{pr_number}")

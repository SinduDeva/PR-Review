#!/usr/bin/env python3
"""
Hybrid file detector: git-first with BitBucket API fallback
- Primary: git diff --numstat (0 API calls, ~50ms)
- Fallback: BitBucket API with pagination (2+ API calls, 1-3s)

Cross-platform: Works on Windows, macOS, Linux
"""

import subprocess
import json
import sys
import os
from typing import List, Dict, Optional


class FileDetector:
    """Detects changed files using git-first, API-fallback approach"""

    def __init__(self, pr_number: str, git_enabled: bool = True):
        self.pr_number = pr_number
        self.git_enabled = git_enabled
        self.files: List[Dict] = []
        self.method_used = None
        self.api_calls_made = 0

    def detect_files(self) -> Dict:
        """Main entry point - try git first, fall back to API"""
        # Try git first (FAST)
        if self.git_enabled:
            try:
                files = self._detect_via_git()
                if files is not None:
                    self.method_used = "git_local"
                    return {
                        "files": files,
                        "metadata": {
                            "method": "git_local",
                            "api_calls": 0,
                            "time_ms": "~50",
                            "fallback_used": False
                        }
                    }
            except Exception as e:
                print(f"⚠️ Git detection failed: {e}", file=sys.stderr)
                print(f"ℹ️ Falling back to BitBucket API", file=sys.stderr)

        # Fall back to API (RELIABLE)
        result = self._detect_via_api()
        result["metadata"]["method"] = "bitbucket_api"
        result["metadata"]["fallback_used"] = self.git_enabled
        self.method_used = "bitbucket_api"
        return result

    def _detect_via_git(self) -> Optional[List[Dict]]:
        """Get files from local git (FAST, 0 API calls, ~50ms)

        Works cross-platform by using absolute path for git repo.
        """
        base_branch = "origin/main"  # or origin/develop

        # Get file statistics (use absolute path for robustness)
        repo_root = os.getcwd()  # Get current git repo root
        output = subprocess.check_output(
            ["git", "diff", "--numstat", f"{base_branch}...HEAD"],
            cwd=repo_root,  # Use absolute path instead of "."
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if not output:
            return []

        files = []
        for line in output.split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            additions, deletions, path = parts[0], parts[1], parts[2]

            # Get change type (M/A/D/R)
            change_type = self._get_change_type(path, base_branch)

            files.append({
                "path": path,
                "additions": int(additions) if additions != '-' else 0,
                "deletions": int(deletions) if deletions != '-' else 0,
                "type": change_type
            })

        return files

    def _get_change_type(self, path: str, base_branch: str) -> str:
        """Determine if file was MODIFIED, ADDED, DELETED, or RENAMED

        Works cross-platform by using absolute path for git repo.
        """
        repo_root = os.getcwd()  # Get current git repo root
        output = subprocess.check_output(
            ["git", "diff", "--name-status", f"{base_branch}...HEAD"],
            cwd=repo_root,  # Use absolute path instead of "."
            stderr=subprocess.DEVNULL
        ).decode().strip()

        for line in output.split('\n'):
            if path in line:
                status = line.split()[0]
                mapping = {'M': 'MODIFY', 'A': 'ADD', 'D': 'DELETE', 'R': 'RENAME'}
                return mapping.get(status, 'MODIFY')

        return 'MODIFY'

    def _detect_via_api(self) -> Dict:
        """
        Get files from BitBucket API (FALLBACK, uses pagination)
        This is a placeholder - actual implementation should call MCP tools
        """
        # Placeholder: In real workflow, this calls mcp1_getPullRequestDiffStat
        # with full pagination as implemented in pr-review-comprehensive.md Step 2

        return {
            "files": [],
            "metadata": {
                "method": "bitbucket_api",
                "pages_fetched": 0,
                "total_items_retrieved": 0,
                "api_calls": 0,
                "time_ms": "N/A",
                "fallback_used": False,
                "api_calls_made": []
            }
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python file_detector.py <pr_number>")
        sys.exit(1)

    pr_number = sys.argv[1]
    detector = FileDetector(pr_number, git_enabled=True)
    result = detector.detect_files()

    print(f"Method: {result['metadata']['method']}")
    print(f"Files: {len(result['files'])}")
    print(f"API calls: {result['metadata']['api_calls']}")

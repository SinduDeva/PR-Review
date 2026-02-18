#!/usr/bin/env python3
"""
PR Number Detection Utility

Detects PR number from multiple sources in order:
1. Command-line argument (--pr)
2. Environment variables (GitHub, GitLab, etc.)
3. Git branch parsing (feature/PROJ-123, PR-456, etc.)
4. Git commit message (Merge pull request #123, Merge branch 'feature/PR-456')

Returns None if PR cannot be detected anywhere.
"""

import os
import subprocess
import re
import sys
from typing import Optional


class PRDetector:
    """Detects PR number from multiple sources"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, msg: str):
        """Log detection attempts"""
        if self.verbose:
            print(f"🔍 {msg}")

    def detect(self, cli_pr: Optional[int] = None) -> Optional[int]:
        """
        Detect PR number from multiple sources

        Args:
            cli_pr: PR number from CLI argument (highest priority)

        Returns:
            PR number if found, None otherwise
        """
        # Priority 1: CLI argument
        if cli_pr:
            self.log(f"✅ PR detected from CLI: {cli_pr}")
            return cli_pr

        # Priority 2: Environment variables
        env_pr = self._detect_from_env()
        if env_pr:
            self.log(f"✅ PR detected from environment: {env_pr}")
            return env_pr

        # Priority 3: Git branch parsing
        git_pr = self._detect_from_git_branch()
        if git_pr:
            self.log(f"✅ PR detected from git branch: {git_pr}")
            return git_pr

        # Priority 4: Git commit message
        commit_pr = self._detect_from_git_commit()
        if commit_pr:
            self.log(f"✅ PR detected from git commit: {commit_pr}")
            return commit_pr

        self.log("❌ PR not found in any source")
        return None

    def _detect_from_env(self) -> Optional[int]:
        """Detect PR from environment variables"""
        self.log("Checking environment variables...")

        # GitHub Actions
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            try:
                pr_num = int(os.environ.get("GITHUB_REF", "").split("/")[-2])
                if pr_num > 0:
                    return pr_num
            except (ValueError, IndexError):
                pass

        # GitHub PR number (alternative)
        if os.environ.get("GITHUB_REF"):
            match = re.search(r"/pull/(\d+)", os.environ.get("GITHUB_REF", ""))
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass

        # GitLab CI
        if os.environ.get("CI_MERGE_REQUEST_IID"):
            try:
                return int(os.environ.get("CI_MERGE_REQUEST_IID"))
            except ValueError:
                pass

        # Bitbucket Cloud
        if os.environ.get("BITBUCKET_PR_ID"):
            try:
                return int(os.environ.get("BITBUCKET_PR_ID"))
            except ValueError:
                pass

        return None

    def _detect_from_git_branch(self) -> Optional[int]:
        """Detect PR from git branch name"""
        self.log("Checking git branch name...")
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()

            if not branch or branch == "HEAD":
                return None

            # Patterns: PR-123, PR/123, PROJ-123, feature/PR-123, feature/123-desc
            patterns = [
                r"PR[-/](\d+)",  # PR-123 or PR/123
                r"feature/PR[-/](\d+)",  # feature/PR-123
                r"(\d+)[-_]",  # 123-description (start with number)
                r"PROJ[-/](\d+)",  # PROJ-123
            ]

            for pattern in patterns:
                match = re.search(pattern, branch, re.IGNORECASE)
                if match:
                    try:
                        pr_num = int(match.group(1))
                        if pr_num > 0:
                            self.log(f"  Branch: {branch}")
                            return pr_num
                    except (ValueError, IndexError):
                        pass

            return None

        except subprocess.CalledProcessError:
            return None

    def _detect_from_git_commit(self) -> Optional[int]:
        """Detect PR from git commit message"""
        self.log("Checking git commit message...")
        try:
            # Get last commit message
            message = subprocess.check_output(
                ["git", "log", "-1", "--format=%B"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()

            # Pattern: "Merge pull request #123 from user/branch"
            match = re.search(r"Merge pull request #(\d+)", message, re.IGNORECASE)
            if match:
                try:
                    pr_num = int(match.group(1))
                    if pr_num > 0:
                        return pr_num
                except (ValueError, IndexError):
                    pass

            # Pattern: "Merge branch 'feature/PR-123'"
            match = re.search(r"Merge branch.*?['\"].*?(?:PR|PROJ)[-/](\d+)", message, re.IGNORECASE)
            if match:
                try:
                    pr_num = int(match.group(1))
                    if pr_num > 0:
                        return pr_num
                except (ValueError, IndexError):
                    pass

            return None

        except subprocess.CalledProcessError:
            return None


def detect_pr_number(cli_pr: Optional[int] = None, verbose: bool = True) -> Optional[int]:
    """
    Convenience function to detect PR number

    Args:
        cli_pr: PR number from CLI argument
        verbose: Enable verbose logging

    Returns:
        PR number if found, None otherwise
    """
    detector = PRDetector(verbose=verbose)
    return detector.detect(cli_pr)


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect PR number from multiple sources"
    )
    parser.add_argument("--pr", type=int, help="PR number (override)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    pr_number = detect_pr_number(cli_pr=args.pr, verbose=not args.quiet)

    if pr_number:
        print(f"\n✅ PR NUMBER: {pr_number}")
        sys.exit(0)
    else:
        print("\n❌ PR NOT FOUND")
        print("\nTried:")
        print("  1. Environment variables (GitHub, GitLab, Bitbucket)")
        print("  2. Git branch name (PR-123, feature/PR-456, etc.)")
        print("  3. Git commit message (Merge pull request #123)")
        print("\nProvide with: --pr <number>")
        sys.exit(1)


if __name__ == "__main__":
    main()

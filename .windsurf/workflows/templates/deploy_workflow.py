#!/usr/bin/env python3
"""
Deploy PR Review Workflow to Other Projects

Safely copies the workflow and templates to other project directories
without overwriting or deleting existing files.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple


class WorkflowDeployer:
    """Deploys PR Review workflow to target projects"""

    def __init__(self, source_dir: str = None, verbose: bool = True):
        """Initialize deployer"""
        self.verbose = verbose

        # Source is the current workflow directory
        if source_dir:
            self.source_dir = Path(source_dir)
        else:
            self.source_dir = Path(".windsurf/workflows")

        self.workflow_file = self.source_dir / "pr-review-comprehensive.md"
        self.templates_dir = self.source_dir / "templates"

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if not self.verbose:
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

    def validate_source(self) -> bool:
        """Validate source workflow files exist"""
        self.log(f"Checking source workflow at: {self.source_dir}", "INFO")

        if not self.workflow_file.exists():
            self.log(f"❌ Workflow file not found: {self.workflow_file}", "ERROR")
            return False

        if not self.templates_dir.exists():
            self.log(f"❌ Templates directory not found: {self.templates_dir}", "ERROR")
            return False

        self.log(f"✅ Source workflow validated", "SUCCESS")
        return True

    def deploy_to_project(self, target_dir: str) -> Tuple[bool, str]:
        """Deploy workflow to target project directory"""
        target_path = Path(target_dir).resolve()

        # Validate target directory exists
        if not target_path.exists():
            return False, f"Target directory does not exist: {target_dir}"

        if not target_path.is_dir():
            return False, f"Target is not a directory: {target_dir}"

        self.log(f"\nDeploying to: {target_path}", "INFO")

        try:
            # Create .windsurf/workflows directory structure
            target_workflows_dir = target_path / ".windsurf" / "workflows"
            target_templates_dir = target_workflows_dir / "templates"

            target_workflows_dir.mkdir(parents=True, exist_ok=True)
            target_templates_dir.mkdir(parents=True, exist_ok=True)

            self.log(f"Created directory structure", "INFO")

            # Copy workflow file
            target_workflow_file = target_workflows_dir / "pr-review-comprehensive.md"
            shutil.copy2(self.workflow_file, target_workflow_file)
            self.log(f"✅ Copied workflow file", "SUCCESS")

            # Copy all template files (but don't delete existing files)
            copied_count = 0
            for template_file in self.templates_dir.glob("*.py"):
                target_template = target_templates_dir / template_file.name
                shutil.copy2(template_file, target_template)
                copied_count += 1

            self.log(f"✅ Copied {copied_count} template files", "SUCCESS")

            # Create .gitignore for generated files
            gitignore_path = target_path / ".gitignore"
            gitignore_content = """
# PR Review Workflow Generated Files
.ai-review/
pr-*.json
pr-*.html
pr-*.txt
"""

            # Append to existing .gitignore if it exists, don't overwrite
            if gitignore_path.exists():
                with open(gitignore_path, 'a') as f:
                    f.write(gitignore_content)
                self.log(f"✅ Updated .gitignore", "SUCCESS")
            else:
                with open(gitignore_path, 'w') as f:
                    f.write(gitignore_content.lstrip())
                self.log(f"✅ Created .gitignore", "SUCCESS")

            self.log(f"✅ Workflow successfully deployed to {target_path.name}", "SUCCESS")
            return True, f"Deployed to {target_path}"

        except Exception as e:
            return False, f"Deployment failed: {e}"

    def deploy_to_multiple(self, target_dirs: List[str]) -> None:
        """Deploy workflow to multiple projects"""
        self.log("PR Review Workflow Deployer", "INFO")
        self.log("=" * 80, "INFO")

        # Validate source
        if not self.validate_source():
            sys.exit(1)

        results = []
        for target_dir in target_dirs:
            success, message = self.deploy_to_project(target_dir)
            results.append((target_dir, success, message))

            if not success:
                self.log(f"❌ {message}", "ERROR")

        # Summary
        self.log("\n" + "=" * 80, "INFO")
        self.log("DEPLOYMENT SUMMARY", "INFO")
        self.log("=" * 80, "INFO")

        successful = sum(1 for _, success, _ in results if success)
        total = len(results)

        for target_dir, success, message in results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            self.log(f"{status}: {target_dir}", "SUCCESS" if success else "ERROR")

        self.log(f"\nTotal: {successful}/{total} successful",
                "SUCCESS" if successful == total else "WARNING")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deploy PR Review Workflow to other projects"
    )
    parser.add_argument(
        "projects",
        nargs="+",
        help="Target project directories to deploy workflow to"
    )
    parser.add_argument(
        "--source",
        default=".windsurf/workflows",
        help="Source workflow directory (default: .windsurf/workflows)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output"
    )

    args = parser.parse_args()

    deployer = WorkflowDeployer(source_dir=args.source, verbose=not args.quiet)
    deployer.deploy_to_multiple(args.projects)


if __name__ == "__main__":
    main()

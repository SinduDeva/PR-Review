#!/usr/bin/env python3
"""
Workflow Lock Manager
Manages workflow file integrity and prevents editing during execution.
Allows unlimited re-runs while protecting against modifications.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Optional


class WorkflowLock:
    """Manages workflow file integrity and locking"""

    LOCK_FILE = '.ai-review/.workflow-lock'
    CHECKSUM_FILE = '.ai-review/.workflow-checksum'

    def __init__(self, workflow_file: str):
        """Initialize lock manager for a workflow file"""
        self.workflow_file = workflow_file
        self.lock_file = Path(self.LOCK_FILE)
        self.checksum_file = Path(self.CHECKSUM_FILE)

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_stored_checksum(self) -> Optional[str]:
        """Get stored workflow checksum"""
        if self.checksum_file.exists():
            try:
                with open(self.checksum_file, 'r') as f:
                    data = json.load(f)
                    return data.get('checksum')
            except Exception:
                return None
        return None

    def _save_checksum(self, checksum: str):
        """Save workflow checksum"""
        self.checksum_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checksum_file, 'w') as f:
            json.dump({
                'checksum': checksum,
                'timestamp': datetime.now().isoformat(),
                'workflow_file': self.workflow_file
            }, f, indent=2)

    def validate_workflow_unchanged(self) -> Tuple[bool, str]:
        """
        Validate that workflow file hasn't been modified.

        Returns:
            (is_valid: bool, message: str)
        """
        if not os.path.exists(self.workflow_file):
            return False, f"Workflow file not found: {self.workflow_file}"

        current_checksum = self._compute_file_hash(self.workflow_file)
        stored_checksum = self._get_stored_checksum()

        if stored_checksum is None:
            # First run - store checksum
            self._save_checksum(current_checksum)
            return True, "First run: Workflow checksum validated"

        if current_checksum != stored_checksum:
            return False, (
                "❌ WORKFLOW FILE MODIFIED\n"
                "   Workflow file has changed since last execution.\n"
                "   To restore, run: git checkout " + self.workflow_file + "\n"
                "   To modify workflow, create a new feature branch."
            )

        return True, "✅ Workflow file unchanged - proceeding"

    def create_lock(self, pr_number: str, run_number: int = 1) -> bool:
        """
        Create execution lock file (for informational purposes only).
        Allows unlimited re-runs.

        Returns:
            True if lock created successfully
        """
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            lock_data = {
                'pr_number': pr_number,
                'run_number': run_number,
                'locked_at': datetime.now().isoformat(),
                'status': 'executing'
            }
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Warning: Could not create lock file: {e}")
            return True  # Don't fail workflow due to lock file issues

    def release_lock(self, success: bool = True) -> bool:
        """
        Release execution lock.

        Returns:
            True if lock released successfully
        """
        try:
            if self.lock_file.exists():
                lock_data = {}
                try:
                    with open(self.lock_file, 'r') as f:
                        lock_data = json.load(f)
                except Exception:
                    pass

                lock_data['status'] = 'completed' if success else 'failed'
                lock_data['released_at'] = datetime.now().isoformat()

                with open(self.lock_file, 'w') as f:
                    json.dump(lock_data, f, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Warning: Could not release lock: {e}")
            return True  # Don't fail workflow due to lock file issues

    def get_lock_status(self) -> Optional[Dict]:
        """Get current lock status"""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def is_rerun_allowed(self, pr_number: str) -> Tuple[bool, str, int]:
        """
        Check if re-run is allowed.
        Re-runs are ALWAYS allowed without cooldown.

        Returns:
            (is_allowed: bool, message: str, run_number: int)
        """
        lock_status = self.get_lock_status()

        if lock_status is None:
            return True, "First run", 1

        # Re-runs are always allowed
        last_pr = lock_status.get('pr_number')
        last_run = lock_status.get('run_number', 0)

        if last_pr == pr_number:
            new_run_number = last_run + 1
            return True, f"Re-run allowed (run #{new_run_number})", new_run_number
        else:
            return True, f"Different PR - starting fresh", 1


def print_lock_status(workflow_file: str):
    """Print workflow lock status"""
    lock = WorkflowLock(workflow_file)

    # Validate workflow unchanged
    is_valid, message = lock.validate_workflow_unchanged()
    print(f"✅ {message}" if is_valid else f"❌ {message}")

    # Check re-run status
    lock_status = lock.get_lock_status()
    if lock_status:
        pr = lock_status.get('pr_number', 'Unknown')
        run = lock_status.get('run_number', 1)
        status = lock_status.get('status', 'unknown')
        print(f"\n📊 Last Execution:")
        print(f"   PR: #{pr}")
        print(f"   Run: #{run}")
        print(f"   Status: {status}")


def main():
    """Command-line interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python workflow_lock.py <workflow_file> [validate|lock|release|status]")
        sys.exit(1)

    workflow_file = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'validate'
    pr_number = sys.argv[3] if len(sys.argv) > 3 else 'unknown'

    lock = WorkflowLock(workflow_file)

    if command == 'validate':
        is_valid, message = lock.validate_workflow_unchanged()
        print(message)
        sys.exit(0 if is_valid else 1)

    elif command == 'lock':
        run_num = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        success = lock.create_lock(pr_number, run_num)
        print(f"✅ Workflow lock created" if success else "❌ Failed to create lock")
        sys.exit(0 if success else 1)

    elif command == 'release':
        success = lock.release_lock(success=True)
        print(f"✅ Workflow lock released" if success else "❌ Failed to release lock")
        sys.exit(0 if success else 1)

    elif command == 'status':
        print_lock_status(workflow_file)
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

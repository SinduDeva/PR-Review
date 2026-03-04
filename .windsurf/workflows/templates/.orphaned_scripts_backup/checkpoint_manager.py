#!/usr/bin/env python3
"""
Checkpoint manager for workflow resume capability.
Saves/loads workflow state to enable resuming from last successful step.
"""

import json
import os
from datetime import datetime, timedelta

class CheckpointManager:
    """Manages workflow checkpoints for resume capability"""

    def __init__(self, pr_number):
        self.pr_number = pr_number
        self.checkpoint_file = f".ai-review/pr-{pr_number}-checkpoint.json"
        self.max_age_hours = 24  # Checkpoints expire after 24 hours

    def save_checkpoint(self, step_number, step_name, partial_data):
        """Save checkpoint after successful step completion"""
        checkpoint = {
            'pr_number': self.pr_number,
            'last_completed_step': step_number,
            'last_step_name': step_name,
            'checkpoint_time': datetime.now().isoformat(),
            'partial_data': partial_data,
            'next_step': step_number + 1,
            'next_step_name': self._get_step_name(step_number + 1)
        }

        os.makedirs('.ai-review', exist_ok=True)
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"✅ Checkpoint saved: Step {step_number} ({step_name}) complete")

    def load_checkpoint(self):
        """Load existing checkpoint if valid"""
        if not os.path.exists(self.checkpoint_file):
            return None

        with open(self.checkpoint_file) as f:
            checkpoint = json.load(f)

        # Check if checkpoint is expired
        checkpoint_time = datetime.fromisoformat(checkpoint['checkpoint_time'])
        age = datetime.now() - checkpoint_time

        if age > timedelta(hours=self.max_age_hours):
            print(f"⚠️ Checkpoint expired (age: {age}). Starting fresh.")
            self.clear_checkpoint()
            return None

        print(f"\n📋 Found checkpoint: Last completed Step {checkpoint['last_completed_step']} ({checkpoint['last_step_name']})")
        print(f"   Next: Step {checkpoint['next_step']} ({checkpoint['next_step_name']})")
        print(f"   Age: {age}")

        return checkpoint

    def clear_checkpoint(self):
        """Remove checkpoint file"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("🗑️ Checkpoint cleared")

    def _get_step_name(self, step_number):
        """Get human-readable step name"""
        steps = {
            0: "PR Detection",
            1: "PR Details",
            2: "File Detection",
            3: "Code Quality Analysis",
            4: "Security Analysis",
            5: "Impact Analysis",
            6: "Report Generation",
            7: "JIRA Integration"
        }
        return steps.get(step_number, f"Step {step_number}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python checkpoint_manager.py <pr_number> load")
        print("  python checkpoint_manager.py <pr_number> clear")
        sys.exit(1)

    pr_number = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "load"

    manager = CheckpointManager(pr_number)

    if action == "load":
        checkpoint = manager.load_checkpoint()
        if checkpoint:
            print(json.dumps(checkpoint, indent=2))
    elif action == "clear":
        manager.clear_checkpoint()

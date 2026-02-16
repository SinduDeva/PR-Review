#!/usr/bin/env python3
"""
Error Handler for PR Review Workflow
Handles errors gracefully while maintaining JSON format integrity.
"""

import json
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable, Any


class ErrorHandler:
    """Central error handling for workflow"""

    def __init__(self):
        """Initialize error handler"""
        self.errors = []
        self.warnings = []

    def log_error(self, step: str, error: Exception, context: str = "") -> Dict:
        """
        Log an error with full context.

        Returns:
            Error entry for JSON logging
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        self.errors.append(error_entry)
        return error_entry

    def log_warning(self, step: str, message: str, context: str = "") -> Dict:
        """
        Log a warning message.

        Returns:
            Warning entry for JSON logging
        """
        warning_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'message': message,
            'context': context
        }
        self.warnings.append(warning_entry)
        return warning_entry

    def safe_execute(
        self,
        step_name: str,
        func: Callable,
        fallback_value: Any = None,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[Dict]]:
        """
        Safely execute a function with error handling.

        Returns:
            (success: bool, result: Any, error_entry: Optional[Dict])
        """
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            error_entry = self.log_error(step_name, e, f"During {step_name} execution")
            print(f"⚠️ Error in {step_name}: {str(e)}")
            return False, fallback_value, error_entry

    def safe_dict_get(
        self,
        data: Dict,
        key_path: str,
        default: Any = None,
        step: str = "unknown"
    ) -> Any:
        """
        Safely retrieve nested dictionary values.

        Args:
            data: Dictionary to traverse
            key_path: Dot-separated path (e.g., "metadata.pr_number")
            default: Default value if not found
            step: Step name for error logging

        Returns:
            Retrieved value or default
        """
        try:
            keys = key_path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return default
            return value if value is not None else default
        except Exception as e:
            self.log_warning(step, f"Could not retrieve {key_path}", str(e))
            return default

    def ensure_json_valid(self, data: Dict, step: str = "unknown") -> Tuple[Dict, List[str]]:
        """
        Ensure JSON structure is valid, filling missing fields.

        Returns:
            (cleaned_data: Dict, errors: List[str])
        """
        errors = []

        # Check required top-level fields
        required_fields = {
            'metadata': {},
            'summary': {},
            'findings': [],
            'files_reviewed': [],
            'files_skipped': [],
            'impact_analysis': {},
            'api_changes': [],
            'spring_boot_validation': {},
            'test_coverage': {},
            'overall_recommendation': {},
            'execution_status': {}
        }

        for field, default_type in required_fields.items():
            if field not in data:
                data[field] = default_type
                errors.append(f"Missing field '{field}' - using default")
            elif type(data[field]) != type(default_type):
                data[field] = default_type
                errors.append(f"Field '{field}' has wrong type - replaced with default")

        return data, errors

    def get_error_summary(self) -> Dict:
        """Get summary of all errors encountered"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': self._build_summary()
        }

    def _build_summary(self) -> str:
        """Build human-readable summary"""
        if not self.errors and not self.warnings:
            return "No errors or warnings"

        summary_parts = []
        if self.errors:
            summary_parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            summary_parts.append(f"{len(self.warnings)} warning(s)")

        return ", ".join(summary_parts)


class StepExecutor:
    """Manages step execution with error recovery"""

    def __init__(self, error_handler: ErrorHandler):
        """Initialize step executor"""
        self.error_handler = error_handler
        self.step_results = {}

    def execute_step(
        self,
        step_name: str,
        step_func: Callable,
        continue_on_error: bool = True,
        fallback_value: Any = None
    ) -> Tuple[bool, Any]:
        """
        Execute a workflow step with error handling.

        Args:
            step_name: Name of the step
            step_func: Function to execute
            continue_on_error: If True, don't fail workflow on error
            fallback_value: Value to use if step fails

        Returns:
            (success: bool, result: Any)
        """
        print(f"\n▶️ Executing: {step_name}")

        success, result, error_entry = self.error_handler.safe_execute(
            step_name,
            step_func,
            fallback_value
        )

        if success:
            print(f"✅ {step_name} completed successfully")
            self.step_results[step_name] = {
                'status': 'success',
                'error': None
            }
        else:
            if continue_on_error:
                print(f"⚠️ {step_name} failed but continuing (using fallback)")
                self.step_results[step_name] = {
                    'status': 'failed_with_fallback',
                    'error': error_entry
                }
            else:
                print(f"❌ {step_name} failed - cannot continue")
                self.step_results[step_name] = {
                    'status': 'failed_fatal',
                    'error': error_entry
                }

        return success, result

    def get_execution_summary(self) -> Dict:
        """Get summary of step execution"""
        total = len(self.step_results)
        successful = sum(1 for r in self.step_results.values() if r['status'] == 'success')
        with_fallback = sum(1 for r in self.step_results.values() if r['status'] == 'failed_with_fallback')
        fatal = sum(1 for r in self.step_results.values() if r['status'] == 'failed_fatal')

        return {
            'total_steps': total,
            'successful_steps': successful,
            'fallback_steps': with_fallback,
            'fatal_failures': fatal,
            'overall_success': fatal == 0,
            'step_results': self.step_results
        }


def handle_missing_json_section(
    data: Dict,
    section_key: str,
    default_structure: Dict,
    error_handler: ErrorHandler
) -> Dict:
    """
    Handle missing JSON sections gracefully.

    Returns:
        Repaired data dictionary
    """
    if section_key not in data:
        error_handler.log_warning(
            "json_repair",
            f"Missing section '{section_key}' - using default structure"
        )
        data[section_key] = default_structure
    elif not isinstance(data[section_key], type(default_structure)):
        error_handler.log_warning(
            "json_repair",
            f"Section '{section_key}' has wrong type - replacing with default"
        )
        data[section_key] = default_structure

    return data


def safe_json_serialization(
    data: Dict,
    output_file: str,
    error_handler: ErrorHandler,
    overwrite: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Safely serialize JSON with error handling.

    Returns:
        (success: bool, output_file: Optional[str])
    """
    try:
        import os

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        # Check if file exists
        if os.path.exists(output_file) and not overwrite:
            error_handler.log_warning(
                "json_save",
                f"File {output_file} already exists and overwrite=False"
            )
            return False, None

        # Write JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON saved successfully: {output_file}")
        return True, output_file

    except Exception as e:
        error_handler.log_error("json_save", e, f"While saving {output_file}")
        return False, None


if __name__ == '__main__':
    # Example usage
    handler = ErrorHandler()
    executor = StepExecutor(handler)

    def example_step():
        return "Step result"

    success, result = executor.execute_step("Example Step", example_step)
    print(f"\n📊 Execution Summary:")
    print(json.dumps(executor.get_execution_summary(), indent=2))

#!/usr/bin/env python3
"""
Metadata Registry

Central registry for metadata schema that allows workflows to query metadata
definitions without reading themselves. This ensures workflow files stay pristine.

Used by:
- Workflow markdown files (to get schema without self-reference)
- All utility modules (for metadata field names and validation)
- Template engines (for rendering metadata fields)
"""

from typing import Dict, List, Any, Tuple
from metadata_constants import (
    MetadataFieldNames,
    MetadataSchema,
    TopLevelSchema,
    create_default_metadata,
    create_default_json_structure,
    validate_metadata_fields,
    get_missing_fields,
    get_all_field_info,
    merge_metadata,
)


class MetadataRegistry:
    """Central registry for metadata schema and operations"""

    @staticmethod
    def get_schema() -> MetadataSchema:
        """Get the complete metadata schema definition"""
        return MetadataSchema

    @staticmethod
    def get_field_names() -> MetadataFieldNames:
        """Get named constants for all metadata field names"""
        return MetadataFieldNames

    @staticmethod
    def get_top_level_schema() -> TopLevelSchema:
        """Get the top-level JSON schema definition"""
        return TopLevelSchema

    @staticmethod
    def get_required_fields() -> List[str]:
        """Get list of all required metadata fields"""
        return MetadataSchema.REQUIRED_FIELDS

    @staticmethod
    def get_optional_fields() -> List[str]:
        """Get list of all optional metadata fields"""
        return MetadataSchema.OPTIONAL_FIELDS

    @staticmethod
    def get_all_fields() -> List[str]:
        """Get list of all metadata fields (required + optional)"""
        return MetadataSchema.ALL_FIELDS

    @staticmethod
    def get_field_type(field_name: str):
        """Get the expected type for a metadata field"""
        return MetadataSchema.FIELD_TYPES.get(field_name)

    @staticmethod
    def get_field_default(field_name: str) -> Any:
        """Get the default value for a metadata field"""
        return MetadataSchema.DEFAULTS.get(field_name)

    @staticmethod
    def get_field_description(field_name: str) -> str:
        """Get human-readable description for a metadata field"""
        return MetadataSchema.DESCRIPTIONS.get(
            field_name,
            f"No description available"
        )

    @staticmethod
    def create_default_metadata(pr_number: str, pr_title: str = "Unknown PR") -> Dict:
        """Create a default metadata dictionary"""
        return create_default_metadata(pr_number, pr_title)

    @staticmethod
    def create_default_structure(pr_number: str, pr_title: str = "Unknown PR") -> Dict:
        """Create a complete default JSON structure"""
        return create_default_json_structure(pr_number, pr_title)

    @staticmethod
    def validate_metadata(data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate metadata against schema.

        Returns:
            (is_valid: bool, errors: List[str])
        """
        return validate_metadata_fields(data)

    @staticmethod
    def get_missing_fields(data: Dict) -> List[str]:
        """Get list of missing required metadata fields"""
        return get_missing_fields(data)

    @staticmethod
    def is_metadata_complete(data: Dict) -> bool:
        """Check if metadata has all required fields"""
        is_valid, _ = validate_metadata_fields(data)
        return is_valid

    @staticmethod
    def merge_metadata(base: Dict, overrides: Dict, preserve_existing: bool = True) -> Dict:
        """Merge metadata overrides into base metadata"""
        return merge_metadata(base, overrides, preserve_existing)

    @staticmethod
    def get_all_field_info() -> Dict[str, Dict[str, Any]]:
        """Get complete information about all metadata fields"""
        return get_all_field_info()

    @staticmethod
    def ensure_metadata_integrity(data: Dict) -> Tuple[Dict, List[str]]:
        """
        Ensure metadata has all required fields, filling missing ones with defaults.

        Returns:
            (cleaned_metadata: Dict, errors: List[str])
        """
        errors = []
        result = data.copy() if isinstance(data, dict) else {}

        # Check for missing required fields
        missing = get_missing_fields(result)
        if missing:
            errors.append(f"Missing fields: {', '.join(missing)}")

            # Try to fill missing fields with defaults
            for field in missing:
                if field in MetadataSchema.DEFAULTS:
                    result[field] = MetadataSchema.DEFAULTS[field]
                    errors.append(f"  Filled '{field}' with default value")
                elif field == MetadataFieldNames.PR_NUMBER:
                    result[field] = 'unknown'
                    errors.append(f"  Filled '{field}' with 'unknown'")
                elif field == MetadataFieldNames.TITLE:
                    result[field] = 'Unknown PR'
                    errors.append(f"  Filled '{field}' with 'Unknown PR'")
                elif field == MetadataFieldNames.REVIEW_ID:
                    import datetime
                    result[field] = f"PR-unknown-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    errors.append(f"  Filled '{field}' with generated ID")

        return result, errors


class MetadataFieldAccessor:
    """Helper class for safe metadata field access"""

    @staticmethod
    def get(metadata: Dict, field_name: str, default: Any = None) -> Any:
        """
        Safely get a metadata field by name (using constants).

        Args:
            metadata: Metadata dictionary
            field_name: Field name (use MetadataFieldNames constant)
            default: Default value if field not found

        Returns:
            Field value or default
        """
        if not isinstance(metadata, dict):
            return default
        return metadata.get(field_name, default)

    @staticmethod
    def set(metadata: Dict, field_name: str, value: Any) -> Dict:
        """
        Safely set a metadata field by name.

        Args:
            metadata: Metadata dictionary
            field_name: Field name (use MetadataFieldNames constant)
            value: Value to set

        Returns:
            Updated metadata dictionary
        """
        if isinstance(metadata, dict):
            metadata[field_name] = value
        return metadata

    @staticmethod
    def extract_branch_display(source: str, target: str) -> str:
        """Create display string for branch field"""
        return f"{source} → {target}"

    @staticmethod
    def update_branch_display(metadata: Dict, source: str = None, target: str = None) -> Dict:
        """Update branch display based on source/target branches"""
        if source is None:
            source = metadata.get(MetadataFieldNames.SOURCE_BRANCH, 'Unknown')
        if target is None:
            target = metadata.get(MetadataFieldNames.TARGET_BRANCH, 'Unknown')

        metadata[MetadataFieldNames.BRANCH] = MetadataFieldAccessor.extract_branch_display(source, target)
        return metadata


class MetadataStringLiterals:
    """
    Deprecated - Use MetadataFieldNames instead.
    Kept for backward compatibility.
    """

    def __getattribute__(self, name):
        import warnings
        warnings.warn(
            "MetadataStringLiterals is deprecated. Use MetadataFieldNames instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return getattr(MetadataFieldNames, name)


# ===== Usage Examples (for documentation) =====

"""
USAGE EXAMPLES:

1. Get metadata schema:
   >>> schema = MetadataRegistry.get_schema()
   >>> print(schema.REQUIRED_FIELDS)

2. Get field names (prevents typos):
   >>> field_names = MetadataRegistry.get_field_names()
   >>> pr_num = metadata[field_names.PR_NUMBER]

3. Create default metadata:
   >>> metadata = MetadataRegistry.create_default_metadata("123", "My PR")

4. Validate metadata:
   >>> is_valid, errors = MetadataRegistry.validate_metadata(metadata)

5. Safe field access:
   >>> accessor = MetadataFieldAccessor()
   >>> pr_num = accessor.get(metadata, MetadataFieldNames.PR_NUMBER, "unknown")
   >>> metadata = accessor.set(metadata, MetadataFieldNames.TITLE, "New Title")

6. Ensure metadata integrity:
   >>> metadata, errors = MetadataRegistry.ensure_metadata_integrity(partial_metadata)

7. Get field info:
   >>> info = MetadataRegistry.get_all_field_info()
   >>> print(info['pr_number']['description'])

In Workflow (.md files):
   Instead of: Reading pr-review-comprehensive.md to get schema
   Do this: from metadata_registry import MetadataRegistry
            schema = MetadataRegistry.get_schema()
"""


if __name__ == '__main__':
    # Test registry
    print("=== Metadata Registry ===\n")

    # Get schema
    schema = MetadataRegistry.get_schema()
    print(f"Required fields: {len(schema.REQUIRED_FIELDS)}")
    print(f"Optional fields: {len(schema.OPTIONAL_FIELDS)}")

    # Get field names
    field_names = MetadataRegistry.get_field_names()
    print(f"\nField name constant: {field_names.PR_NUMBER}")

    # Create default metadata
    metadata = MetadataRegistry.create_default_metadata("456", "Test PR 2")
    print(f"\nDefault metadata created:")
    print(f"  PR: {metadata[field_names.PR_NUMBER]}")
    print(f"  Title: {metadata[field_names.TITLE]}")

    # Validate
    is_valid, errors = MetadataRegistry.validate_metadata(metadata)
    print(f"\nValidation: {is_valid}")

    # Get all field info
    all_info = MetadataRegistry.get_all_field_info()
    print(f"\nTotal fields: {len(all_info)}")
    print(f"PR Number field info: {all_info[field_names.PR_NUMBER]}")

    print("\n✅ Metadata registry ready for use")
